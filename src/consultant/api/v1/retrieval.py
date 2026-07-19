from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from consultant.api.dependencies import (
    CurrentIdentity,
    DocumentCatalog,
    Embeddings,
    ProjectStore,
    RetrievalReranker,
)
from consultant.application.retrieval import RetrievalHit, RetrievalService

router = APIRouter(tags=["retrieval"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=8, ge=1, le=20)


class SearchResponse(BaseModel):
    hits: list[RetrievalHit]


@router.post("/projects/{project_id}/retrieval:search", response_model=SearchResponse)
async def search(
    project_id: UUID,
    request: SearchRequest,
    identity: CurrentIdentity,
    projects: ProjectStore,
    catalog: DocumentCatalog,
    embeddings: Embeddings,
    reranker: RetrievalReranker,
) -> SearchResponse:
    hits = await RetrievalService(
        projects=projects,
        catalog=catalog,
        embeddings=embeddings,
        reranker=reranker,
    ).search(
        identity=identity,
        project_id=project_id,
        query=request.query,
        top_k=request.top_k,
    )
    return SearchResponse(hits=hits)
