import pytest

from consultant.agents.delivery_agent import build_delivery_plan
from consultant.agents.proposal_agent import build_proposal
from consultant.agents.schemas import RequirementItemOutput
from consultant.domain.common import ValidationFailure


def test_proposal_rejects_new_unapproved_commitment() -> None:
    with pytest.raises(ValidationFailure, match="unapproved"):
        build_proposal(
            title="Proposal",
            approved_sections={"scope": "客服试点"},
            commitments=["三天上线"],
            approved_commitments=set(),
            citation_ids=["CIT-001"],
        )


def test_delivery_plan_traces_every_requirement_to_acceptance() -> None:
    requirement = RequirementItemOutput(
        id="REQ-1", title="响应", description="缩短响应", priority="must",
        claim_kind="fact", citation_ids=["CIT-1"]
    )
    plan = build_delivery_plan(requirements=[requirement], criteria={"REQ-1": "P95 < 3 秒"})
    assert plan.acceptance_criteria[0].requirement_id == "REQ-1"
