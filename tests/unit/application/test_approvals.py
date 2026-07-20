from uuid import uuid4

import pytest

from consultant.application.approvals import ApprovalService, InMemoryApprovalStore
from consultant.application.business_loop import (
    BusinessLoopService,
    InMemoryBusinessObjectRepository,
)
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.business_loop import ApprovalDecision, BusinessObjectKind, ReviewStatus


@pytest.mark.asyncio
async def test_approval_snapshot_stays_immutable_and_upstream_change_marks_stale() -> None:
    identity = Identity(uuid4(), uuid4(), "Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    repository = InMemoryBusinessObjectRepository()
    business = BusinessLoopService(projects=projects, repository=repository)
    upstream = await business.create(
        identity=identity,
        project_id=project.id,
        kind=BusinessObjectKind.REQUIREMENT_BASELINE,
        title="Requirements",
        payload={"goal": "A"},
    )
    downstream = await business.create(
        identity=identity,
        project_id=project.id,
        kind=BusinessObjectKind.PROPOSAL,
        title="Proposal",
        payload={"scope": "A"},
    )
    service = ApprovalService(
        projects=projects, objects=repository, approvals=InMemoryApprovalStore()
    )
    approval = await service.submit(
        identity=identity,
        project_id=project.id,
        target_kind=downstream.kind,
        target_id=downstream.id,
        target_version=1,
        depends_on={upstream.id},
    )
    approved = await service.decide(
        identity=identity,
        project_id=project.id,
        approval_id=approval.id,
        decision=ApprovalDecision.APPROVED,
        expected_target_version=1,
        comment="ok",
    )
    await business.revise(
        identity=identity,
        project_id=project.id,
        item_id=upstream.id,
        expected_version=1,
        payload={"goal": "B"},
    )

    current = await business.get(
        identity=identity, project_id=project.id, item_id=downstream.id
    )
    assert current.status == ReviewStatus.APPROVED
    assert current.stale is True
    assert approved.snapshot == approval.snapshot
