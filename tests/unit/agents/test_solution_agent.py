from uuid import uuid4

import pytest

from consultant.adapters.llm.fake_model import FakeStructuredModel
from consultant.agents.schemas import RequirementAnalysisOutput, SolutionDesignOutput
from consultant.agents.solution_agent import run_solution_agent
from consultant.application.projects import Identity
from consultant.application.retrieval import RetrievalHit


@pytest.mark.asyncio
async def test_solution_agent_uses_confirmed_baseline_and_citations(
    identity: Identity, evidence_hit: RetrievalHit
) -> None:
    async def search(**kwargs: object) -> list[RetrievalHit]:
        del kwargs
        return [evidence_hit]

    baseline = RequirementAnalysisOutput(
        summary="需要报告自动化",
        claims=[],
        requirements=[],
        information_gaps=[],
        interview_questions=[],
    )
    model = FakeStructuredModel(
        [
            {
                "executive_summary": "建设自动化报告场景",
                "scenarios": [
                    {
                        "id": "SCN-001",
                        "name": "自动化经营报告",
                        "business_problem": "人工汇总耗时",
                        "priority": "now",
                        "feasibility": "high",
                        "citation_ids": ["CIT-001"],
                    }
                ],
                "recommended_scope": ["数据汇总"],
                "technical_components": ["RAG"],
                "integration_boundaries": ["只读数据源"],
                "risks": ["源数据质量"],
                "open_questions": [],
            }
        ]
    )

    state = await run_solution_agent(
        model=model,
        search=search,
        identity=identity,
        project_id=str(uuid4()),
        objective="设计 AI 方案",
        requirement_baseline=baseline,
    )

    assert state["status"] == "completed"
    assert isinstance(state["draft"], SolutionDesignOutput)
