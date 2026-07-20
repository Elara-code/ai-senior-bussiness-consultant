from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from consultant.adapters.export.docx import DocxExporter
from consultant.adapters.export.markdown import MarkdownExporter
from consultant.adapters.export.pdf import PdfExporter
from consultant.api.dependencies import (
    BusinessObjects,
    CurrentIdentity,
    MemoryObjectStore,
    ProjectStore,
)
from consultant.application.exports import ExportResult, ExportService
from consultant.ports.exporter import DocumentExporter

router = APIRouter(prefix="/projects/{project_id}/exports", tags=["exports"])


class ExportRequest(BaseModel):
    item_id: UUID
    format: Literal["markdown", "docx", "pdf"]
    citation_lines: list[str] = Field(default_factory=list)


@router.post("", response_model=ExportResult)
async def create_export(
    project_id: UUID,
    request: ExportRequest,
    identity: CurrentIdentity,
    projects: ProjectStore,
    objects: BusinessObjects,
    object_store: MemoryObjectStore,
) -> ExportResult:
    exporters: dict[str, DocumentExporter] = {
        "markdown": MarkdownExporter(),
        "docx": DocxExporter(),
        "pdf": PdfExporter(),
    }
    return await ExportService(
        projects=projects, objects=objects, object_store=object_store
    ).export(
        identity=identity,
        project_id=project_id,
        item_id=request.item_id,
        exporter=exporters[request.format],
        citation_lines=request.citation_lines,
    )
