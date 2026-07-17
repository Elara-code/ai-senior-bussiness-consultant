from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from consultant.domain.common import new_id, utc_now


class DeliverableKind(StrEnum):
    REQUIREMENT_BASELINE = "requirement_baseline"
    SCENARIO_MATRIX = "scenario_matrix"
    SOLUTION_DRAFT = "solution_draft"


class DeliverableRevision(BaseModel):
    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    deliverable_id: UUID
    version_number: int = Field(ge=1)
    kind: DeliverableKind
    payload: dict[str, Any]
    rendered_markdown: str
    source_run_id: UUID
    created_at: datetime = Field(default_factory=utc_now)
