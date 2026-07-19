from dataclasses import dataclass
from typing import Any
from uuid import UUID

from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.common import NotFound, ValidationFailure, new_id
from consultant.domain.deliverables import (
    CitationRecord,
    Deliverable,
    DeliverableKind,
    DeliverableRevision,
)
from consultant.domain.documents import DocumentStatus


@dataclass(frozen=True, slots=True)
class CitationInput:
    chunk_id: UUID
    quote: str


class InMemoryDeliverableStore:
    def __init__(self) -> None:
        self.deliverables: dict[UUID, Deliverable] = {}
        self.revisions: dict[UUID, list[DeliverableRevision]] = {}
        self.citations: dict[UUID, list[CitationRecord]] = {}
        self.dependencies: dict[UUID, set[UUID]] = {}


class DeliverableService:
    def __init__(
        self,
        *,
        projects: InMemoryProjectStore,
        documents: InMemoryDocumentCatalog,
        store: InMemoryDeliverableStore,
    ) -> None:
        self._projects = projects
        self._documents = documents
        self._store = store

    def create_revision(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        kind: DeliverableKind,
        title: str,
        payload: dict[str, Any],
        rendered_markdown: str,
        source_run_id: UUID,
        citations: list[CitationInput],
        deliverable_id: UUID | None = None,
    ) -> tuple[Deliverable, DeliverableRevision, list[CitationRecord]]:
        self._projects.get_visible(identity=identity, project_id=project_id)
        deliverable = self._resolve_deliverable(
            identity=identity,
            project_id=project_id,
            kind=kind,
            title=title,
            deliverable_id=deliverable_id,
        )
        previous = self._store.revisions.setdefault(deliverable.id, [])
        revision = DeliverableRevision(
            organization_id=identity.organization_id,
            project_id=project_id,
            deliverable_id=deliverable.id,
            version_number=len(previous) + 1,
            kind=kind,
            payload=payload,
            rendered_markdown=rendered_markdown,
            source_run_id=source_run_id,
        )
        records = [
            self._validate_citation(
                identity=identity,
                project_id=project_id,
                revision_id=revision.id,
                citation=item,
            )
            for item in citations
        ]
        previous.append(revision)
        self._store.citations[revision.id] = records
        self._store.dependencies[revision.id] = {
            record.document_version_id for record in records
        }
        deliverable.stale = False
        return (
            deliverable.model_copy(deep=True),
            revision.model_copy(deep=True),
            [record.model_copy(deep=True) for record in records],
        )

    def list_for_project(
        self, *, identity: Identity, project_id: UUID
    ) -> list[Deliverable]:
        self._projects.get_visible(identity=identity, project_id=project_id)
        return [
            item.model_copy(deep=True)
            for item in self._store.deliverables.values()
            if item.organization_id == identity.organization_id and item.project_id == project_id
        ]

    def get(
        self, *, identity: Identity, deliverable_id: UUID
    ) -> tuple[Deliverable, DeliverableRevision, list[CitationRecord]]:
        deliverable = self._visible(identity=identity, deliverable_id=deliverable_id)
        revisions = self._store.revisions.get(deliverable_id, [])
        if not revisions:
            raise NotFound("Deliverable revision not found")
        current = revisions[-1]
        return (
            deliverable.model_copy(deep=True),
            current.model_copy(deep=True),
            [item.model_copy(deep=True) for item in self._store.citations.get(current.id, [])],
        )

    def list_revisions(
        self, *, identity: Identity, deliverable_id: UUID
    ) -> list[DeliverableRevision]:
        self._visible(identity=identity, deliverable_id=deliverable_id)
        return [item.model_copy(deep=True) for item in self._store.revisions[deliverable_id]]

    def mark_stale_for_document_version(self, document_version_id: UUID) -> set[UUID]:
        affected: set[UUID] = set()
        for deliverable_id, revisions in self._store.revisions.items():
            if any(
                document_version_id in self._store.dependencies.get(revision.id, set())
                for revision in revisions
            ):
                self._store.deliverables[deliverable_id].stale = True
                affected.add(deliverable_id)
        return affected

    def _resolve_deliverable(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        kind: DeliverableKind,
        title: str,
        deliverable_id: UUID | None,
    ) -> Deliverable:
        if deliverable_id is not None:
            deliverable = self._visible(identity=identity, deliverable_id=deliverable_id)
            if deliverable.project_id != project_id or deliverable.kind != kind:
                raise ValidationFailure("Deliverable kind or project cannot change")
            return deliverable
        deliverable = Deliverable(
            organization_id=identity.organization_id,
            project_id=project_id,
            kind=kind,
            title=title,
        )
        self._store.deliverables[deliverable.id] = deliverable
        return deliverable

    def _validate_citation(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        revision_id: UUID,
        citation: CitationInput,
    ) -> CitationRecord:
        chunk = self._documents.chunks.get(citation.chunk_id)
        if (
            chunk is None
            or chunk.organization_id != identity.organization_id
            or chunk.project_id != project_id
        ):
            raise ValidationFailure("Citation chunk is outside the project scope")
        version = self._documents.versions.get(chunk.document_version_id)
        if version is None or version.status != DocumentStatus.READY:
            raise ValidationFailure("Citation document version is not ready")
        normalized_quote = " ".join(citation.quote.split())
        if normalized_quote not in " ".join(chunk.content.split()):
            raise ValidationFailure("Citation quote is not present in the source chunk")
        return CitationRecord(
            id=new_id(),
            organization_id=identity.organization_id,
            project_id=project_id,
            revision_id=revision_id,
            document_version_id=version.id,
            chunk_id=chunk.id,
            quote=normalized_quote,
            content_hash=chunk.content_hash,
        )

    def _visible(self, *, identity: Identity, deliverable_id: UUID) -> Deliverable:
        deliverable = self._store.deliverables.get(deliverable_id)
        if deliverable is None or deliverable.organization_id != identity.organization_id:
            raise NotFound("Deliverable not found")
        self._projects.get_visible(identity=identity, project_id=deliverable.project_id)
        return deliverable
