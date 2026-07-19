from typing import Any

from consultant.adapters.llm.fake_model import FakeStructuredModel
from consultant.agents.requirement_agent import run_requirement_agent
from consultant.agents.schemas import RequirementAnalysisOutput
from consultant.agents.solution_agent import run_solution_agent
from consultant.application.projects import Identity
from consultant.application.retrieval import RetrievalHit, RetrievalService
from consultant.domain.agent_runs import AgentKind, AgentRun


class DemoAgentExecutor:
    """Deterministic offline executor used by the local demo and CI."""

    def __init__(self, retrieval: RetrievalService) -> None:
        self._retrieval = retrieval

    async def __call__(self, run: AgentRun) -> dict[str, Any]:
        identity = Identity(
            organization_id=run.organization_id,
            user_id=run.actor_id,
            display_name="Demo Consultant",
        )

        async def search(**kwargs: Any) -> list[RetrievalHit]:
            return await self._retrieval.search(**kwargs)

        hits = await self._retrieval.search(
            identity=identity,
            project_id=run.project_id,
            query=run.objective,
            top_k=8,
        )
        citations = ["CIT-001"] if hits else []
        if run.agent_kind == AgentKind.REQUIREMENT_ANALYSIS:
            response = {
                "summary": "根据项目材料形成需求分析。" if hits else "当前资料不足。",
                "claims": (
                    [
                        {
                            "text": hits[0].content,
                            "kind": "fact",
                            "citation_ids": citations,
                        }
                    ]
                    if hits
                    else []
                ),
                "requirements": [],
                "information_gaps": [] if hits else ["客户业务材料"],
                "interview_questions": [] if hits else ["请补充当前业务流程。"],
            }
            state = await run_requirement_agent(
                model=FakeStructuredModel([response]),
                search=search,
                identity=identity,
                project_id=str(run.project_id),
                objective=run.objective,
            )
        else:
            response = {
                "executive_summary": "基于已确认需求形成演示方案。",
                "scenarios": (
                    [
                        {
                            "id": "SCN-001",
                            "name": "自动化报告",
                            "business_problem": "人工处理效率低",
                            "priority": "now",
                            "feasibility": "high",
                            "citation_ids": citations,
                        }
                    ]
                    if hits
                    else []
                ),
                "recommended_scope": ["报告生成"],
                "technical_components": ["RAG", "Agent"],
                "integration_boundaries": ["演示模式不写入外部系统"],
                "risks": ["源数据质量"],
                "open_questions": [],
            }
            baseline = RequirementAnalysisOutput(
                summary="演示需求基线",
                claims=[],
                requirements=[],
                information_gaps=[],
                interview_questions=[],
            )
            state = await run_solution_agent(
                model=FakeStructuredModel([response]),
                search=search,
                identity=identity,
                project_id=str(run.project_id),
                objective=run.objective,
                requirement_baseline=baseline,
            )
        draft = state.get("draft")
        return {
            "status": state["status"],
            "draft": draft.model_dump(mode="json") if draft is not None else None,
            "quality_issues": state.get("quality_issues", []),
        }
