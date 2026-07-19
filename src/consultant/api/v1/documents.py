from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status
from pydantic import BaseModel

from consultant.api.dependencies import (
    CurrentIdentity,
    DocumentCatalog,
    MemoryObjectStore,
    ProjectStore,
    RequestSettings,
)
from consultant.application.ingestion import DocumentIngestionService
from consultant.domain.documents import DocumentStatus, DocumentVersion

router = APIRouter(tags=["documents"])


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    version_id: UUID
    filename: str
    status: DocumentStatus
    content_hash: str


async def _file_stream(file: UploadFile) -> AsyncIterator[bytes]:
    while chunk := await file.read(1024 * 1024):
        yield chunk


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    project_id: UUID,
    identity: CurrentIdentity,
    project_store: ProjectStore,
    catalog: DocumentCatalog,
    object_store: MemoryObjectStore,
    settings: RequestSettings,
    file: Annotated[UploadFile, File()],
) -> DocumentUploadResponse:
    result = await DocumentIngestionService(
        project_store=project_store,
        catalog=catalog,
        object_store=object_store,
        max_upload_bytes=settings.max_upload_bytes,
    ).upload(
        identity=identity,
        project_id=project_id,
        filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        stream=_file_stream(file),
    )
    return DocumentUploadResponse(
        document_id=result.document.id,
        version_id=result.version.id,
        filename=result.version.filename,
        status=result.version.status,
        content_hash=result.version.content_hash,
    )


@router.get("/projects/{project_id}/documents", response_model=list[DocumentVersion])
def list_documents(
    project_id: UUID,
    identity: CurrentIdentity,
    project_store: ProjectStore,
    catalog: DocumentCatalog,
) -> list[DocumentVersion]:
    project_store.get_visible(identity=identity, project_id=project_id)
    return catalog.list_for_project(project_id)
