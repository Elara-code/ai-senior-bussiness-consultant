from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.agent_runs import AgentKind, AgentRun, AgentRunStatus
from consultant.domain.common import Conflict, NotFound, utc_now
from consultant.ports.event_store import EventStore, RunEvent

AgentRunner = Callable[[AgentRun], Awaitable[dict[str, Any]]]


class AgentRunService:
    def __init__(self, *, projects: InMemoryProjectStore, events: EventStore) -> None:
        self._projects = projects
        self._events = events
        self._runs: dict[UUID, AgentRun] = {}
        self._idempotency: dict[tuple[UUID, UUID, str], UUID] = {}
        self._sequences: dict[UUID, int] = {}
        self._results: dict[UUID, dict[str, Any]] = {}

    async def create(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        agent_kind: AgentKind,
        objective: str,
        idempotency_key: str,
    ) -> tuple[AgentRun, bool]:
        self._projects.get_visible(identity=identity, project_id=project_id)
        key = (identity.organization_id, identity.user_id, idempotency_key)
        if existing_id := self._idempotency.get(key):
            existing = self._runs[existing_id]
            if existing.project_id != project_id or existing.agent_kind != agent_kind:
                raise Conflict("Idempotency key was already used for a different request")
            return existing.model_copy(deep=True), False
        run = AgentRun(
            organization_id=identity.organization_id,
            project_id=project_id,
            actor_id=identity.user_id,
            agent_kind=agent_kind,
            objective=objective,
            idempotency_key=idempotency_key,
        )
        self._runs[run.id] = run
        self._idempotency[key] = run.id
        self._sequences[run.id] = 0
        return run.model_copy(deep=True), True

    def get_visible(self, *, identity: Identity, run_id: UUID) -> AgentRun:
        run = self._runs.get(run_id)
        if run is None or run.organization_id != identity.organization_id:
            raise NotFound("Agent run not found")
        self._projects.get_visible(identity=identity, project_id=run.project_id)
        return run.model_copy(deep=True)

    async def execute(self, *, run_id: UUID, runner: AgentRunner) -> None:
        run = self._require(run_id)
        run.transition_to(AgentRunStatus.RUNNING)
        await self._publish(run, "run.started", {"status": run.status.value})
        try:
            result = await runner(run.model_copy(deep=True))
            if run.status == AgentRunStatus.CANCELLED:
                return
            self._results[run.id] = result
            if result.get("requires_approval"):
                run.checkpoint = {
                    "completed_step": result.get("completed_step"),
                    "result_id": result.get("result_id"),
                }
                run.transition_to(AgentRunStatus.AWAITING_APPROVAL)
                await self._publish(
                    run,
                    "approval.required",
                    {"status": run.status.value, "checkpoint": run.checkpoint},
                )
                return
            run.transition_to(AgentRunStatus.COMPLETED)
            await self._publish(run, "run.completed", {"status": run.status.value})
        except Exception as error:
            if run.status != AgentRunStatus.CANCELLED:
                run.transition_to(AgentRunStatus.FAILED)
                await self._publish(
                    run,
                    "run.failed",
                    {"status": run.status.value, "code": "AGENT_EXECUTION_FAILED"},
                )
            raise error

    async def publish_plan(self, *, run_id: UUID, steps: list[dict[str, Any]]) -> None:
        await self._publish(self._require(run_id), "plan.created", {"steps": steps})

    async def publish_step(
        self, *, run_id: UUID, step_id: str, completed: bool = False
    ) -> None:
        await self._publish(
            self._require(run_id),
            "step.completed" if completed else "step.started",
            {"step_id": step_id},
        )

    async def resume_after_approval(
        self, *, identity: Identity, run_id: UUID, runner: AgentRunner
    ) -> None:
        run = self._require(run_id)
        self._projects.get_visible(identity=identity, project_id=run.project_id)
        if run.status != AgentRunStatus.AWAITING_APPROVAL:
            raise Conflict("Agent run is not awaiting approval")
        run.transition_to(AgentRunStatus.RUNNING)
        await self._publish(run, "run.resumed", {"status": run.status.value})
        try:
            result = await runner(run.model_copy(deep=True))
            self._results[run.id] = result
            run.transition_to(AgentRunStatus.COMPLETED)
            await self._publish(run, "run.completed", {"status": run.status.value})
        except Exception:
            run.transition_to(AgentRunStatus.FAILED)
            await self._publish(
                run, "run.failed", {"status": run.status.value, "code": "AGENT_RESUME_FAILED"}
            )
            raise

    async def cancel(self, *, identity: Identity, run_id: UUID) -> AgentRun:
        run = self._require(run_id)
        self._projects.get_visible(identity=identity, project_id=run.project_id)
        if run.organization_id != identity.organization_id:
            raise NotFound("Agent run not found")
        if run.status in {
            AgentRunStatus.COMPLETED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
        }:
            return run.model_copy(deep=True)
        run.transition_to(AgentRunStatus.CANCELLED)
        await self._publish(run, "run.cancelled", {"status": run.status.value})
        return run.model_copy(deep=True)

    def result(self, run_id: UUID) -> dict[str, Any] | None:
        return self._results.get(run_id)

    @property
    def events(self) -> EventStore:
        return self._events

    def _require(self, run_id: UUID) -> AgentRun:
        try:
            return self._runs[run_id]
        except KeyError as error:
            raise NotFound("Agent run not found") from error

    async def _publish(self, run: AgentRun, event_type: str, payload: dict[str, Any]) -> None:
        sequence = self._sequences[run.id] + 1
        self._sequences[run.id] = sequence
        await self._events.append(
            RunEvent(
                run_id=run.id,
                sequence=sequence,
                event_type=event_type,
                payload=payload,
                occurred_at=utc_now(),
            )
        )
