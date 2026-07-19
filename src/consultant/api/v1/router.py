from fastapi import APIRouter

from consultant.api.v1.documents import router as documents_router
from consultant.api.v1.projects import router as projects_router
from consultant.api.v1.retrieval import router as retrieval_router

router = APIRouter(prefix="/api/v1")
router.include_router(projects_router)
router.include_router(documents_router)
router.include_router(retrieval_router)
