from consultant.agents.planning import build_consultant_plan
from consultant.domain.projects import ProjectStage


def test_supervisor_plan_has_dependencies_and_approval_gates() -> None:
    plan = build_consultant_plan(ProjectStage.DISCOVERY)
    assert [step.id for step in plan] == [
        "requirements", "solution", "value_risk", "proposal", "delivery", "knowledge"
    ]
    assert plan[1].depends_on == ("requirements",)
    assert plan[0].approval_required is True
    assert plan[-1].approval_required is True


def test_plan_starts_from_current_project_stage() -> None:
    assert build_consultant_plan(ProjectStage.DELIVERY)[0].id == "delivery"
