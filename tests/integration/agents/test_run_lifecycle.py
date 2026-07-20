from uuid import uuid4

import pytest

from consultant.adapters.events.memory import InMemoryEventStore
from consultant.application.agent_service import AgentRunService
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.agent_runs import AgentKind, AgentRunStatus


@pytest.mark.asyncio
async def test_run_lifecycle_is_idempotent_and_emits_terminal_event() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    events = InMemoryEventStore()
    service = AgentRunService(projects=projects, events=events)

    first, created = await service.create(
        identity=identity,
        project_id=project.id,
        agent_kind=AgentKind.REQUIREMENT_ANALYSIS,
        objective="Analyze",
        idempotency_key="request-0001",
    )
    second, created_again = await service.create(
        identity=identity,
        project_id=project.id,
        agent_kind=AgentKind.REQUIREMENT_ANALYSIS,
        objective="Analyze",
        idempotency_key="request-0001",
    )

    async def runner(run: object) -> dict[str, str]:
        del run
        return {"result": "ok"}

    await service.execute(run_id=first.id, runner=runner)
    stored = service.get_visible(identity=identity, run_id=first.id)
    run_events = await events.list_after(run_id=first.id, sequence=0)

    assert created is True
    assert created_again is False
    assert first.id == second.id
    assert stored.status == AgentRunStatus.COMPLETED
    assert [event.event_type for event in run_events] == ["run.started", "run.completed"]


@pytest.mark.asyncio
async def test_run_pauses_for_approval_and_resumes_from_checkpoint() -> None:
    identity = Identity(uuid4(), uuid4(), "Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    events = InMemoryEventStore()
    service = AgentRunService(projects=projects, events=events)
    run, _ = await service.create(
        identity=identity,
        project_id=project.id,
        agent_kind=AgentKind.SOLUTION_DESIGN,
        objective="Design",
        idempotency_key="approval-0001",
    )

    async def pause_runner(run: object) -> dict[str, object]:
        del run
        return {"requires_approval": True, "completed_step": "solution", "result_id": "S1"}

    async def resume_runner(run: object) -> dict[str, object]:
        del run
        return {"result": "complete"}

    await service.execute(run_id=run.id, runner=pause_runner)
    paused = service.get_visible(identity=identity, run_id=run.id)
    assert paused.status == AgentRunStatus.AWAITING_APPROVAL
    assert paused.checkpoint == {"completed_step": "solution", "result_id": "S1"}

    await service.resume_after_approval(identity=identity, run_id=run.id, runner=resume_runner)
    emitted = await events.list_after(run_id=run.id, sequence=0)
    assert service.get_visible(identity=identity, run_id=run.id).status == AgentRunStatus.COMPLETED
    assert [event.event_type for event in emitted] == [
        "run.started", "approval.required", "run.resumed", "run.completed"
    ]
