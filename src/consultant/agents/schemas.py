from typing import Literal

from pydantic import BaseModel, Field


class ClaimOutput(BaseModel):
    text: str = Field(min_length=1)
    kind: Literal["fact", "inference", "assumption"]
    citation_ids: list[str] = Field(default_factory=list)


class RequirementItemOutput(BaseModel):
    id: str
    title: str
    description: str
    priority: Literal["must", "should", "could", "wont"]
    claim_kind: Literal["fact", "inference", "assumption"]
    citation_ids: list[str] = Field(default_factory=list)


class RequirementAnalysisOutput(BaseModel):
    summary: str
    claims: list[ClaimOutput]
    requirements: list[RequirementItemOutput]
    information_gaps: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)


class ScenarioOutput(BaseModel):
    id: str
    name: str
    business_problem: str
    priority: Literal["now", "next", "later", "not_recommended"]
    feasibility: Literal["high", "medium", "low", "unknown"]
    citation_ids: list[str] = Field(default_factory=list)


class SolutionDesignOutput(BaseModel):
    executive_summary: str
    scenarios: list[ScenarioOutput]
    recommended_scope: list[str]
    technical_components: list[str]
    integration_boundaries: list[str]
    risks: list[str]
    open_questions: list[str] = Field(default_factory=list)
