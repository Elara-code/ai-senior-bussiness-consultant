from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from consultant.domain.common import Conflict, InvalidStateTransition, new_id, utc_now


class BusinessObjectKind(StrEnum):
    REQUIREMENT_BASELINE = "requirement_baseline"
    SCENARIO_ASSESSMENT = "scenario_assessment"
    BUSINESS_CASE = "business_case"
    PROPOSAL = "proposal"
    DELIVERY_PLAN = "delivery_plan"
    KNOWLEDGE_CANDIDATE = "knowledge_candidate"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PublicationStatus(StrEnum):
    CANDIDATE = "candidate"
    PUBLISHED = "published"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class EvidenceStatement(BaseModel):
    text: str = Field(min_length=1)
    kind: Literal["fact", "inference", "assumption"]
    citation_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_fact_citation(self) -> Self:
        if self.kind == "fact" and not self.citation_ids:
            raise ValueError("facts require at least one citation")
        return self


class BusinessParameter(BaseModel):
    name: str = Field(min_length=1)
    value: float
    unit: str = ""
    source: str | None = None
    citation_id: UUID | None = None
    confirmed_by: UUID | None = None

    @model_validator(mode="after")
    def require_traceability(self) -> Self:
        if self.source is None and self.citation_id is None and self.confirmed_by is None:
            raise ValueError("business parameters require a source or human confirmation")
        return self


class VersionedBusinessObject(BaseModel):
    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    kind: BusinessObjectKind
    title: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]
    statements: list[EvidenceStatement] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    status: ReviewStatus = ReviewStatus.DRAFT
    stale: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def revise(
        self,
        *,
        payload: dict[str, Any],
        expected_version: int,
        title: str | None = None,
        statements: list[EvidenceStatement] | None = None,
    ) -> VersionedBusinessObject:
        if self.version != expected_version:
            raise Conflict("Business object version has changed")
        revised = self.model_copy(deep=True)
        revised.version += 1
        revised.payload = payload
        revised.title = title or self.title
        revised.statements = statements if statements is not None else self.statements
        revised.status = ReviewStatus.DRAFT
        revised.stale = False
        revised.updated_at = utc_now()
        return revised

    def submit_for_approval(self) -> None:
        if self.status not in {ReviewStatus.DRAFT, ReviewStatus.REJECTED}:
            raise InvalidStateTransition(f"Cannot submit {self.status} object")
        self.status = ReviewStatus.AWAITING_APPROVAL
        self.updated_at = utc_now()

    def approve(self) -> None:
        if self.status != ReviewStatus.AWAITING_APPROVAL:
            raise InvalidStateTransition(f"Cannot approve {self.status} object")
        self.status = ReviewStatus.APPROVED
        self.updated_at = utc_now()

    def reject(self) -> None:
        if self.status != ReviewStatus.AWAITING_APPROVAL:
            raise InvalidStateTransition(f"Cannot reject {self.status} object")
        self.status = ReviewStatus.REJECTED
        self.updated_at = utc_now()


RequirementBaseline = VersionedBusinessObject
ScenarioAssessment = VersionedBusinessObject
BusinessCase = VersionedBusinessObject
Proposal = VersionedBusinessObject
DeliveryPlan = VersionedBusinessObject


class Approval(BaseModel):
    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    target_kind: BusinessObjectKind
    target_id: UUID
    target_version: int = Field(ge=1)
    snapshot: dict[str, Any]
    submitted_by: UUID
    decision: ApprovalDecision = ApprovalDecision.PENDING
    reviewer_id: UUID | None = None
    comment: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None

    def replace_snapshot(self, snapshot: dict[str, Any]) -> None:
        if self.decision != ApprovalDecision.PENDING:
            raise InvalidStateTransition("A decided approval snapshot is immutable")
        self.snapshot = snapshot

    def decide(
        self,
        *,
        decision: ApprovalDecision,
        reviewer_id: UUID,
        comment: str = "",
    ) -> None:
        if self.decision != ApprovalDecision.PENDING:
            raise InvalidStateTransition("Approval has already been decided")
        if decision == ApprovalDecision.PENDING:
            raise InvalidStateTransition("A decision must be final")
        self.decision = decision
        self.reviewer_id = reviewer_id
        self.comment = comment
        self.decided_at = utc_now()


class KnowledgeCandidate(BaseModel):
    business_object: VersionedBusinessObject
    publication_status: PublicationStatus = PublicationStatus.CANDIDATE
    redaction_issues: list[str] = Field(default_factory=list)

    def publish(self) -> None:
        if self.business_object.status != ReviewStatus.APPROVED:
            raise InvalidStateTransition("Knowledge must be approved before publication")
        if self.redaction_issues:
            raise InvalidStateTransition("Redaction issues must be resolved")
        self.publication_status = PublicationStatus.PUBLISHED


class WorkflowExecution(BaseModel):
    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    workflow_id: str = Field(min_length=1)
    workflow_version: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=255)
    input_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    output: dict[str, Any] | None = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    error_code: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
