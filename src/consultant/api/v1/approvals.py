from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from consultant.api.dependencies import (
    ApprovalStore,
    BusinessObjects,
    CurrentIdentity,
    ProjectStore,
)
from consultant.application.approvals import ApprovalService
from consultant.domain.business_loop import Approval, ApprovalDecision, BusinessObjectKind

router = APIRouter(prefix="/projects/{project_id}/approvals", tags=["approvals"])


class SubmitApprovalRequest(BaseModel):
    target_kind: BusinessObjectKind
    target_id: UUID
    target_version: int = Field(ge=1)
    depends_on: set[UUID] = Field(default_factory=set)


class DecideApprovalRequest(BaseModel):
    decision: ApprovalDecision
    expected_target_version: int = Field(ge=1)
    comment: str = Field(default="", max_length=4000)


@router.post("", response_model=Approval, status_code=status.HTTP_201_CREATED)
async def submit_approval(
    project_id: UUID,
    request: SubmitApprovalRequest,
    identity: CurrentIdentity,
    projects: ProjectStore,
    objects: BusinessObjects,
    approvals: ApprovalStore,
) -> Approval:
    return await ApprovalService(
        projects=projects, objects=objects, approvals=approvals
    ).submit(
        identity=identity,
        project_id=project_id,
        target_kind=request.target_kind,
        target_id=request.target_id,
        target_version=request.target_version,
        depends_on=request.depends_on,
    )


@router.get("", response_model=list[Approval])
def list_approvals(
    project_id: UUID,
    identity: CurrentIdentity,
    projects: ProjectStore,
    objects: BusinessObjects,
    approvals: ApprovalStore,
) -> list[Approval]:
    return list(
        ApprovalService(projects=projects, objects=objects, approvals=approvals).list(
            identity=identity, project_id=project_id
        )
    )


@router.post("/{approval_id}/decision", response_model=Approval)
async def decide_approval(
    project_id: UUID,
    approval_id: UUID,
    request: DecideApprovalRequest,
    identity: CurrentIdentity,
    projects: ProjectStore,
    objects: BusinessObjects,
    approvals: ApprovalStore,
) -> Approval:
    return await ApprovalService(
        projects=projects, objects=objects, approvals=approvals
    ).decide(
        identity=identity,
        project_id=project_id,
        approval_id=approval_id,
        decision=request.decision,
        expected_target_version=request.expected_target_version,
        comment=request.comment,
    )
