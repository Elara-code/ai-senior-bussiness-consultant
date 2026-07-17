from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from consultant.domain.common import InvalidStateTransition, new_id, utc_now


class AgentKind(StrEnum):
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    SOLUTION_DESIGN = "solution_design"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_INPUT = "awaiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_RUN_TRANSITIONS: dict[AgentRunStatus, frozenset[AgentRunStatus]] = {
    AgentRunStatus.QUEUED: frozenset({AgentRunStatus.RUNNING, AgentRunStatus.CANCELLED}),
    AgentRunStatus.RUNNING: frozenset(
        {
            AgentRunStatus.AWAITING_INPUT,
            AgentRunStatus.COMPLETED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
        }
    ),
    AgentRunStatus.AWAITING_INPUT: frozenset(
        {AgentRunStatus.RUNNING, AgentRunStatus.CANCELLED}
    ),
    AgentRunStatus.COMPLETED: frozenset(),
    AgentRunStatus.FAILED: frozenset({AgentRunStatus.QUEUED}),
    AgentRunStatus.CANCELLED: frozenset(),
}


class AgentRun(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    actor_id: UUID
    agent_kind: AgentKind
    objective: str = Field(min_length=1, max_length=4000)
    status: AgentRunStatus = AgentRunStatus.QUEUED
    idempotency_key: str = Field(min_length=8, max_length=255)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def transition_to(self, target: AgentRunStatus) -> None:
        if target == self.status:
            return
        if target not in _RUN_TRANSITIONS[self.status]:
            raise InvalidStateTransition(f"Cannot move agent run from {self.status} to {target}")
        self.status = target
        self.updated_at = utc_now()
