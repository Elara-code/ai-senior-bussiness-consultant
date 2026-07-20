from fastapi import APIRouter

from consultant.api.v1.agent_runs import router as agent_runs_router
from consultant.api.v1.approvals import router as approvals_router
from consultant.api.v1.business_cases import router as business_cases_router
from consultant.api.v1.deliverables import router as deliverables_router
from consultant.api.v1.delivery_plans import router as delivery_plans_router
from consultant.api.v1.documents import router as documents_router
from consultant.api.v1.projects import router as projects_router
from consultant.api.v1.proposals import router as proposals_router
from consultant.api.v1.requirements import router as requirements_router
from consultant.api.v1.retrieval import router as retrieval_router
from consultant.api.v1.scenarios import router as scenarios_router

router = APIRouter(prefix="/api/v1")
router.include_router(projects_router)
router.include_router(documents_router)
router.include_router(retrieval_router)
router.include_router(agent_runs_router)
router.include_router(deliverables_router)
router.include_router(requirements_router)
router.include_router(scenarios_router)
router.include_router(business_cases_router)
router.include_router(proposals_router)
router.include_router(delivery_plans_router)
router.include_router(approvals_router)
