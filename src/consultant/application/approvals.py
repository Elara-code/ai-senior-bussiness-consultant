from collections.abc import Sequence
from uuid import UUID

from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.business_loop import (
    Approval,
    ApprovalDecision,
    BusinessObjectKind,
)
from consultant.domain.common import Conflict, Forbidden, NotFound
from consultant.domain.projects import ProjectRole
from consultant.ports.business_loop import BusinessObjectRepository


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self.approvals: dict[UUID, Approval] = {}

    def add(self, approval: Approval) -> None:
        self.approvals[approval.id] = approval.model_copy(deep=True)

    def save(self, approval: Approval) -> None:
        if approval.id not in self.approvals:
            raise NotFound("Approval not found")
        self.approvals[approval.id] = approval.model_copy(deep=True)

    def get(self, approval_id: UUID) -> Approval | None:
        approval = self.approvals.get(approval_id)
        return approval.model_copy(deep=True) if approval is not None else None

    def list_for_project(self, organization_id: UUID, project_id: UUID) -> Sequence[Approval]:
        return [
            approval.model_copy(deep=True)
            for approval in self.approvals.values()
            if approval.organization_id == organization_id and approval.project_id == project_id
        ]


class ApprovalService:
    def __init__(
        self,
        *,
        projects: InMemoryProjectStore,
        objects: BusinessObjectRepository,
        approvals: InMemoryApprovalStore,
    ) -> None:
        self._projects = projects
        self._objects = objects
        self._approvals = approvals

    async def submit(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        target_kind: BusinessObjectKind,
        target_id: UUID,
        target_version: int,
        depends_on: set[UUID] | None = None,
    ) -> Approval:
        role = self._projects.role_for(identity=identity, project_id=project_id)
        if role == ProjectRole.VIEWER:
            raise Forbidden("Viewers cannot submit approvals")
        target = await self._objects.get_latest(
            organization_id=identity.organization_id,
            project_id=project_id,
            item_id=target_id,
        )
        if target is None or target.kind != target_kind:
            raise NotFound("Approval target not found")
        if target.version != target_version:
            raise Conflict("Approval target version has changed")
        target.submit_for_approval()
        await self._objects.save_state(target)
        if depends_on:
            await self._objects.link_dependencies(
                organization_id=identity.organization_id,
                project_id=project_id,
                upstream_ids=depends_on,
                downstream_id=target_id,
            )
        approval = Approval(
            organization_id=identity.organization_id,
            project_id=project_id,
            target_kind=target_kind,
            target_id=target.id,
            target_version=target.version,
            snapshot=target.model_dump(mode="json"),
            submitted_by=identity.user_id,
        )
        self._approvals.add(approval)
        return approval.model_copy(deep=True)

    async def decide(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        approval_id: UUID,
        decision: ApprovalDecision,
        expected_target_version: int,
        comment: str = "",
    ) -> Approval:
        if self._projects.role_for(identity=identity, project_id=project_id) != ProjectRole.OWNER:
            raise Forbidden("Only project owners can decide approvals")
        approval = self._visible(
            identity=identity, project_id=project_id, approval_id=approval_id
        )
        target = await self._objects.get_latest(
            organization_id=identity.organization_id,
            project_id=project_id,
            item_id=approval.target_id,
        )
        if target is None:
            raise NotFound("Approval target not found")
        if target.version != expected_target_version or target.version != approval.target_version:
            raise Conflict("Approval target version has changed")
        approval.decide(
            decision=decision,
            reviewer_id=identity.user_id,
            comment=comment,
        )
        if decision == ApprovalDecision.APPROVED:
            target.approve()
        else:
            target.reject()
        await self._objects.save_state(target)
        self._approvals.save(approval)
        return approval.model_copy(deep=True)

    def list(self, *, identity: Identity, project_id: UUID) -> Sequence[Approval]:
        self._projects.get_visible(identity=identity, project_id=project_id)
        return self._approvals.list_for_project(identity.organization_id, project_id)

    def _visible(
        self, *, identity: Identity, project_id: UUID, approval_id: UUID
    ) -> Approval:
        approval = self._approvals.get(approval_id)
        if (
            approval is None
            or approval.organization_id != identity.organization_id
            or approval.project_id != project_id
        ):
            raise NotFound("Approval not found")
        return approval
