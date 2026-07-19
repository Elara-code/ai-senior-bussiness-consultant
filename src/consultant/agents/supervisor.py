from typing import Literal


def route_agent(task: str) -> Literal["requirement_analysis", "solution_design"]:
    normalized = task.lower()
    solution_terms = ("方案", "架构", "solution", "architecture", "场景")
    if any(term in normalized for term in solution_terms):
        return "solution_design"
    return "requirement_analysis"
