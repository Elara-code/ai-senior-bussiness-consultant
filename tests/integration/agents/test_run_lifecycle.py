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
