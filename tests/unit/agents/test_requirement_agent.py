from uuid import uuid4

import pytest

from consultant.adapters.llm.fake_model import FakeStructuredModel
from consultant.agents.requirement_agent import run_requirement_agent
from consultant.agents.schemas import RequirementAnalysisOutput
from consultant.application.projects import Identity
from consultant.application.retrieval import RetrievalHit


@pytest.mark.asyncio
async def test_requirement_agent_completes_with_valid_fact_citation(
    identity: Identity, evidence_hit: RetrievalHit
) -> None:
    async def search(**kwargs: object) -> list[RetrievalHit]:
        del kwargs
        return [evidence_hit]

    model = FakeStructuredModel(
        [
            {
                "summary": "报告依赖人工汇总。",
                "claims": [
                    {"text": "三名员工手工汇总", "kind": "fact", "citation_ids": ["CIT-001"]}
                ],
                "requirements": [
                    {
                        "id": "REQ-001",
                        "title": "报告自动化",
                        "description": "自动汇总经营数据",
                        "priority": "must",
                        "claim_kind": "inference",
                        "citation_ids": ["CIT-001"],
                    }
                ],
                "information_gaps": [],
                "interview_questions": [],
            }
        ]
    )

    state = await run_requirement_agent(
        model=model,
        search=search,
        identity=identity,
        project_id=str(uuid4()),
        objective="形成需求基线",
    )

    assert state["status"] == "completed"
    assert isinstance(state["draft"], RequirementAnalysisOutput)
    assert state["quality_issues"] == []


@pytest.mark.asyncio
async def test_requirement_agent_fails_fact_without_citation(
    identity: Identity, evidence_hit: RetrievalHit
) -> None:
    async def search(**kwargs: object) -> list[RetrievalHit]:
        del kwargs
        return [evidence_hit]

    model = FakeStructuredModel(
        [
            {
                "summary": "报告依赖人工汇总。",
                "claims": [{"text": "没有证据", "kind": "fact", "citation_ids": []}],
                "requirements": [],
                "information_gaps": [],
                "interview_questions": [],
            }
        ]
    )

    state = await run_requirement_agent(
        model=model,
        search=search,
        identity=identity,
        project_id=str(uuid4()),
        objective="形成需求基线",
        max_quality_retries=0,
    )

    assert state["status"] == "failed"
    assert "requires at least one citation" in state["quality_issues"][0]
