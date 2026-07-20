from consultant.agents.schemas import (
    AcceptanceCriterionOutput,
    DeliveryPlanOutput,
    RequirementItemOutput,
)
from consultant.domain.common import ValidationFailure


def build_delivery_plan(
    *, requirements: list[RequirementItemOutput], criteria: dict[str, str]
) -> DeliveryPlanOutput:
    missing = [item.id for item in requirements if item.id not in criteria]
    if missing:
        raise ValidationFailure(
            f"Requirements lack acceptance criteria: {', '.join(missing)}"
        )
    return DeliveryPlanOutput(
        milestones=["需求确认", "试点上线", "验收移交"],
        acceptance_criteria=[
            AcceptanceCriterionOutput(requirement_id=item.id, criterion=criteria[item.id])
            for item in requirements
        ],
        training_items=["管理员培训", "最终用户培训"],
    )
