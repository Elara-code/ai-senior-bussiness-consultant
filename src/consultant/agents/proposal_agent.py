from consultant.agents.schemas import ProposalOutput
from consultant.domain.common import ValidationFailure


def build_proposal(
    *,
    title: str,
    approved_sections: dict[str, str],
    commitments: list[str],
    approved_commitments: set[str],
    citation_ids: list[str],
) -> ProposalOutput:
    unauthorized = sorted(set(commitments) - approved_commitments)
    if unauthorized:
        raise ValidationFailure(
            f"Proposal contains unapproved commitments: {', '.join(unauthorized)}"
        )
    return ProposalOutput(
        title=title,
        sections=approved_sections,
        commitments=commitments,
        citation_ids=citation_ids,
    )
