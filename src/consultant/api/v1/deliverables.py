from typing import Any
from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from consultant.api.dependencies import (
    CurrentIdentity,
    DeliverableStore,
    DocumentCatalog,
    ProjectStore,
)
from consultant.application.deliverables import CitationInput, DeliverableService
from consultant.domain.deliverables import (
    CitationRecord,
    Deliverable,
    DeliverableKind,
    DeliverableRevision,
)

router = APIRouter(tags=["deliverables"])


class CitationRequest(BaseModel):
    chunk_id: UUID
    quote: str = Field(min_length=1, max_length=1200)


class CreateRevisionRequest(BaseModel):
    deliverable_id: UUID | None = None
    kind: DeliverableKind
    title: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]
    rendered_markdown: str
    source_run_id: UUID
    citations: list[CitationRequest] = Field(default_factory=list)


class DeliverableResponse(BaseModel):
    deliverable: Deliverable
    revision: DeliverableRevision
    citations: list[CitationRecord]


@router.post(
    "/projects/{project_id}/deliverables",
    response_model=DeliverableResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deliverable_revision(
    project_id: UUID,
    request: CreateRevisionRequest,
    identity: CurrentIdentity,
    projects: ProjectStore,
    documents: DocumentCatalog,
    store: DeliverableStore,
) -> DeliverableResponse:
    deliverable, revision, citations = DeliverableService(
        projects=projects, documents=documents, store=store
    ).create_revision(
        identity=identity,
        project_id=project_id,
        kind=request.kind,
        title=request.title,
        payload=request.payload,
        rendered_markdown=request.rendered_markdown,
        source_run_id=request.source_run_id,
        citations=[
            CitationInput(chunk_id=item.chunk_id, quote=item.quote)
            for item in request.citations
        ],
        deliverable_id=request.deliverable_id,
    )
    return DeliverableResponse(
        deliverable=deliverable, revision=revision, citations=citations
    )


@router.get("/projects/{project_id}/deliverables", response_model=list[Deliverable])
def list_deliverables(
    project_id: UUID,
    identity: CurrentIdentity,
    projects: ProjectStore,
    documents: DocumentCatalog,
    store: DeliverableStore,
) -> list[Deliverable]:
    return DeliverableService(
        projects=projects, documents=documents, store=store
    ).list_for_project(identity=identity, project_id=project_id)


@router.get("/deliverables/{deliverable_id}", response_model=DeliverableResponse)
def get_deliverable(
    deliverable_id: UUID,
    identity: CurrentIdentity,
    projects: ProjectStore,
    documents: DocumentCatalog,
    store: DeliverableStore,
) -> DeliverableResponse:
    deliverable, revision, citations = DeliverableService(
        projects=projects, documents=documents, store=store
    ).get(identity=identity, deliverable_id=deliverable_id)
    return DeliverableResponse(
        deliverable=deliverable, revision=revision, citations=citations
    )


@router.get(
    "/deliverables/{deliverable_id}/revisions",
    response_model=list[DeliverableRevision],
)
def list_deliverable_revisions(
    deliverable_id: UUID,
    identity: CurrentIdentity,
    projects: ProjectStore,
    documents: DocumentCatalog,
    store: DeliverableStore,
) -> list[DeliverableRevision]:
    return DeliverableService(
        projects=projects, documents=documents, store=store
    ).list_revisions(identity=identity, deliverable_id=deliverable_id)
