from typing import Literal, TypedDict

from consultant.agents.schemas import RequirementAnalysisOutput, SolutionDesignOutput


class PlanStep(TypedDict):
    id: str
    name: str
    status: Literal["pending", "running", "completed", "failed"]


class AgentEvidence(TypedDict):
    id: str
    chunk_id: str
    document_title: str
    content: str
    section: str | None
    page_start: int | None


class ConsultantAgentState(TypedDict, total=False):
    schema_version: str
    run_id: str
    organization_id: str
    project_id: str
    actor_id: str
    agent_kind: Literal[
        "requirement_analysis", "solution_design", "value_risk", "proposal", "delivery", "knowledge"
    ]
    objective: str
    status: Literal[
        "planning",
        "retrieving",
        "analyzing",
        "reviewing",
        "awaiting_input",
        "awaiting_approval",
        "completed",
        "failed",
        "cancelled",
    ]
    plan: list[PlanStep]
    current_step: int
    max_steps: int
    evidence: list[AgentEvidence]
    requirement_baseline: RequirementAnalysisOutput
    draft: RequirementAnalysisOutput | SolutionDesignOutput
    quality_issues: list[str]
    retry_count: int
    max_quality_retries: int
    input_tokens: int
    output_tokens: int
    model: str
    model_request_id: str | None
