import re

from consultant.agents.schemas import KnowledgeOutput
from consultant.domain.business_loop import ReviewStatus
from consultant.domain.common import InvalidStateTransition

_SENSITIVE_PATTERNS = (
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b1[3-9]\d{9}\b"),
    re.compile(r"(?i)(客户名称|联系人|账号)\s*[:：]\s*[^,，;；\n]+"),
)


def create_knowledge_candidate(
    *, title: str, content: str, source_status: ReviewStatus
) -> KnowledgeOutput:
    if source_status != ReviewStatus.APPROVED:
        raise InvalidStateTransition("Only approved content can become knowledge")
    redacted = content
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub("[已脱敏]", redacted)
    remaining = [label for label in ("客户名称", "联系人", "账号") if label in redacted]
    return KnowledgeOutput(
        title=title,
        reusable_pattern="经审批项目实践",
        redacted_content=redacted,
        redaction_issues=remaining,
    )
