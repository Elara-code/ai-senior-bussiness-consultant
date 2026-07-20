import pytest

from consultant.agents.knowledge_agent import create_knowledge_candidate
from consultant.domain.business_loop import ReviewStatus
from consultant.domain.common import InvalidStateTransition


def test_knowledge_agent_only_accepts_approved_and_redacts_sensitive_data() -> None:
    with pytest.raises(InvalidStateTransition):
        create_knowledge_candidate(title="Case", content="x", source_status=ReviewStatus.DRAFT)
    output = create_knowledge_candidate(
        title="Case",
        content="客户名称：渡河株式会社，联系人：张三，电话 13800138000 test@example.com",
        source_status=ReviewStatus.APPROVED,
    )
    assert "渡河" not in output.redacted_content
    assert "13800138000" not in output.redacted_content
    assert "test@example.com" not in output.redacted_content
