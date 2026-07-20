import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.business_loop import ReviewStatus
from consultant.domain.common import NotFound
from consultant.ports.business_loop import BusinessObjectRepository
from consultant.ports.exporter import DocumentExporter, ExportDocument
from consultant.ports.object_store import ObjectStore


@dataclass(frozen=True, slots=True)
class ExportResult:
    object_key: str
    filename: str
    content_type: str
    approved: bool


class ExportService:
    def __init__(
        self,
        *,
        projects: InMemoryProjectStore,
        objects: BusinessObjectRepository,
        object_store: ObjectStore,
    ) -> None:
        self._projects = projects
        self._objects = objects
        self._object_store = object_store

    async def export(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        item_id: UUID,
        exporter: DocumentExporter,
        citation_lines: list[str] | None = None,
    ) -> ExportResult:
        self._projects.get_visible(identity=identity, project_id=project_id)
        item = await self._objects.get_latest(
            organization_id=identity.organization_id, project_id=project_id, item_id=item_id
        )
        if item is None:
            raise NotFound("Business object not found")
        body = "```json\n" + json.dumps(item.payload, ensure_ascii=False, indent=2) + "\n```"
        exported = exporter.export(
            ExportDocument(
                title=item.title,
                body_markdown=body,
                approved=item.status == ReviewStatus.APPROVED,
                citation_lines=citation_lines or [],
            )
        )
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", item.title).strip("-") or "deliverable"
        filename = f"{safe_name}-v{item.version}.{exported.extension}"
        key = (
            f"organizations/{identity.organization_id}/projects/{project_id}"
            f"/exports/{item.id}/{filename}"
        )

        async def stream() -> AsyncIterator[bytes]:
            yield exported.content

        await self._object_store.put_stream(
            key=key, stream=stream(), content_type=exported.content_type
        )
        return ExportResult(
            key, filename, exported.content_type, item.status == ReviewStatus.APPROVED
        )
