from dataclasses import dataclass

from consultant.domain.projects import ProjectStage


@dataclass(frozen=True, slots=True)
class ConsultantPlanStep:
    id: str
    name: str
    depends_on: tuple[str, ...] = ()
    approval_required: bool = False


def build_consultant_plan(stage: ProjectStage) -> list[ConsultantPlanStep]:
    discovery = ConsultantPlanStep("requirements", "形成需求基线", approval_required=True)
    solution = ConsultantPlanStep(
        "solution", "设计场景与方案", ("requirements",), approval_required=True
    )
    value = ConsultantPlanStep(
        "value_risk", "评估价值与风险", ("solution",), approval_required=True
    )
    proposal = ConsultantPlanStep("proposal", "撰写客户提案", ("value_risk",))
    delivery = ConsultantPlanStep("delivery", "形成交付计划", ("proposal",))
    knowledge = ConsultantPlanStep("knowledge", "提取知识候选", ("delivery",), True)
    plans = [discovery, solution, value, proposal, delivery, knowledge]
    start = {
        ProjectStage.DISCOVERY: 0,
        ProjectStage.REQUIREMENTS: 0,
        ProjectStage.SOLUTION: 1,
        ProjectStage.PROPOSAL: 3,
        ProjectStage.DELIVERY: 4,
        ProjectStage.CLOSED: 5,
    }[stage]
    return plans[start:]
