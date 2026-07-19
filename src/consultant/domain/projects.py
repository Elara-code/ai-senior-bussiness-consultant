from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from consultant.domain.common import InvalidStateTransition, new_id, utc_now


class ProjectStage(StrEnum):
    DISCOVERY = "discovery"
    REQUIREMENTS = "requirements"
    SOLUTION = "solution"
    PROPOSAL = "proposal"
    DELIVERY = "delivery"
    CLOSED = "closed"


class ProjectRole(StrEnum):
    OWNER = "owner"
    CONSULTANT = "consultant"
    VIEWER = "viewer"


_STAGE_TRANSITIONS: dict[ProjectStage, frozenset[ProjectStage]] = {
    ProjectStage.DISCOVERY: frozenset({ProjectStage.REQUIREMENTS, ProjectStage.CLOSED}),
    ProjectStage.REQUIREMENTS: frozenset(
        {ProjectStage.DISCOVERY, ProjectStage.SOLUTION, ProjectStage.CLOSED}
    ),
    ProjectStage.SOLUTION: frozenset(
        {ProjectStage.REQUIREMENTS, ProjectStage.PROPOSAL, ProjectStage.CLOSED}
    ),
    ProjectStage.PROPOSAL: frozenset(
        {ProjectStage.SOLUTION, ProjectStage.DELIVERY, ProjectStage.CLOSED}
    ),
    ProjectStage.DELIVERY: frozenset({ProjectStage.PROPOSAL, ProjectStage.CLOSED}),
    ProjectStage.CLOSED: frozenset(),
}


class Project(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    stage: ProjectStage = ProjectStage.DISCOVERY
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def transition_to(self, target: ProjectStage) -> None:
        if target == self.stage:
            return
        if target not in _STAGE_TRANSITIONS[self.stage]:
            raise InvalidStateTransition(f"Cannot move project from {self.stage} to {target}")
        self.stage = target
        self.updated_at = utc_now()
