from uuid import uuid4

import pytest
from pydantic import ValidationError

from consultant.domain.business_loop import (
    Approval,
    ApprovalDecision,
    BusinessObjectKind,
    BusinessParameter,
    EvidenceStatement,
    ReviewStatus,
    VersionedBusinessObject,
)
from consultant.domain.common import InvalidStateTransition


def test_fact_requires_at_least_one_citation() -> None:
    with pytest.raises(ValidationError, match="facts require"):
        EvidenceStatement(text="客户有 300 名坐席", kind="fact")


def test_business_parameter_requires_a_source_or_confirmation() -> None:
    with pytest.raises(ValidationError, match="source"):
        BusinessParameter(name="人工成本", value=1000)


def test_business_object_uses_governed_review_transitions() -> None:
    item = VersionedBusinessObject(
        organization_id=uuid4(),
        project_id=uuid4(),
        kind=BusinessObjectKind.REQUIREMENT_BASELINE,
        title="需求基线",
        payload={"goals": ["缩短响应时间"]},
    )

    item.submit_for_approval()
    assert item.status == ReviewStatus.AWAITING_APPROVAL
    item.approve()
    assert item.status == ReviewStatus.APPROVED
    with pytest.raises(InvalidStateTransition):
        item.submit_for_approval()


def test_approved_snapshot_is_immutable() -> None:
    approval = Approval(
        organization_id=uuid4(),
        project_id=uuid4(),
        target_kind=BusinessObjectKind.PROPOSAL,
        target_id=uuid4(),
        target_version=2,
        snapshot={"title": "客户方案"},
        submitted_by=uuid4(),
    )
    approval.decide(
        decision=ApprovalDecision.APPROVED,
        reviewer_id=uuid4(),
        comment="同意",
    )

    with pytest.raises(InvalidStateTransition):
        approval.replace_snapshot({"title": "changed"})


@pytest.mark.parametrize("kind", list(BusinessObjectKind))
def test_all_phase_two_business_object_kinds_can_be_versioned(
    kind: BusinessObjectKind,
) -> None:
    item = VersionedBusinessObject(
        organization_id=uuid4(),
        project_id=uuid4(),
        kind=kind,
        title=kind.value,
        payload={},
    )
    revised = item.revise(payload={"version": 2}, expected_version=1)
    assert revised.version == 2
    assert revised.id == item.id
