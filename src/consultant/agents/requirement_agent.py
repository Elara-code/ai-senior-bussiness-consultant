from importlib.resources import files
from typing import Any, cast
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from consultant.agents.nodes import (
    SearchFunction,
    build_analysis_node,
    build_retrieve_node,
    plan_node,
    review_node,
    route_after_review,
)
from consultant.agents.schemas import RequirementAnalysisOutput
from consultant.agents.state import ConsultantAgentState
from consultant.application.projects import Identity
from consultant.ports.model import StructuredModel


def build_requirement_graph(
    *, model: StructuredModel, search: SearchFunction, identity: Identity
) -> Any:
    prompt = files("consultant.agents.prompts").joinpath("requirement_system.md").read_text()
    graph = StateGraph(ConsultantAgentState)
    graph.add_node("plan", plan_node)
    retrieve_node: Any = build_retrieve_node(search=search, identity=identity)
    analyze_node: Any = build_analysis_node(
        model=model,
        output_schema=RequirementAnalysisOutput,
        system_prompt=prompt,
    )
    graph.add_node("retrieve", retrieve_node)
    graph.add_node(
        "analyze",
        analyze_node,
    )
    graph.add_node("review", review_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "review")
    graph.add_conditional_edges(
        "review", route_after_review, {"retry": "analyze", "finish": END}
    )
    return graph.compile()


async def run_requirement_agent(
    *,
    model: StructuredModel,
    search: SearchFunction,
    identity: Identity,
    project_id: str,
    objective: str,
    max_quality_retries: int = 1,
) -> ConsultantAgentState:
    initial: ConsultantAgentState = {
        "schema_version": "1.0",
        "run_id": str(uuid4()),
        "organization_id": str(identity.organization_id),
        "project_id": project_id,
        "actor_id": str(identity.user_id),
        "agent_kind": "requirement_analysis",
        "objective": objective,
        "status": "planning",
        "max_steps": 12,
        "max_quality_retries": max_quality_retries,
    }
    result = await build_requirement_graph(
        model=model, search=search, identity=identity
    ).ainvoke(initial)
    return cast(ConsultantAgentState, result)
