import hashlib
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import PurePath
from uuid import UUID

from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.common import Conflict, ValidationFailure, new_id
from consultant.domain.documents import DocumentChunk, DocumentVersion, SourceDocument
from consultant.ports.object_store import ObjectStore

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/plain",
}


@dataclass(slots=True)
class UploadResult:
    document: SourceDocument
    version: DocumentVersion


class InMemoryDocumentCatalog:
    def __init__(self) -> None:
        self.documents: dict[UUID, SourceDocument] = {}
        self.versions: dict[UUID, DocumentVersion] = {}
        self._hash_index: dict[tuple[UUID, str], UUID] = {}
        self.chunks: dict[UUID, DocumentChunk] = {}

    def add(self, document: SourceDocument, version: DocumentVersion) -> None:
        key = (document.project_id, version.content_hash)
        if key in self._hash_index:
            raise Conflict("This document content already exists in the project")
        self.documents[document.id] = document
        self.versions[version.id] = version
        self._hash_index[key] = version.id

    def remove(self, document_id: UUID, version_id: UUID) -> None:
        version = self.versions.pop(version_id, None)
        self.documents.pop(document_id, None)
        if version is not None:
            self._hash_index.pop((version.project_id, version.content_hash), None)

    def list_for_project(self, project_id: UUID) -> list[DocumentVersion]:
        return [
            version.model_copy(deep=True)
            for version in self.versions.values()
            if version.project_id == project_id
        ]

    def get_version(self, version_id: UUID) -> DocumentVersion:
        try:
            return self.versions[version_id]
        except KeyError as error:
            raise ValidationFailure("Document version does not exist") from error

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            self.chunks[chunk.id] = chunk


class DocumentIngestionService:
    def __init__(
        self,
        *,
        project_store: InMemoryProjectStore,
        catalog: InMemoryDocumentCatalog,
        object_store: ObjectStore,
        max_upload_bytes: int,
    ) -> None:
        self._projects = project_store
        self._catalog = catalog
        self._objects = object_store
        self._max_upload_bytes = max_upload_bytes

    async def upload(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        filename: str,
        content_type: str,
        stream: AsyncIterator[bytes],
    ) -> UploadResult:
        self._projects.get_visible(identity=identity, project_id=project_id)
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationFailure(f"Unsupported content type: {content_type}")
        safe_filename = PurePath(filename.replace("\\", "/")).name.strip()
        if not safe_filename or safe_filename in {".", ".."}:
            raise ValidationFailure("Invalid filename")

        document = SourceDocument(
            organization_id=identity.organization_id,
            project_id=project_id,
            title=safe_filename,
        )
        version_id = new_id()
        object_key = (
            f"{identity.organization_id}/{project_id}/{document.id}/{version_id}/{safe_filename}"
        )
        digest = hashlib.sha256()
        size = 0

        async def validated_stream() -> AsyncIterator[bytes]:
            nonlocal size
            async for chunk in stream:
                size += len(chunk)
                if size > self._max_upload_bytes:
                    raise ValidationFailure("File exceeds the configured upload limit")
                digest.update(chunk)
                yield chunk

        try:
            await self._objects.put_stream(
                key=object_key,
                stream=validated_stream(),
                content_type=content_type,
            )
            if size == 0:
                raise ValidationFailure("Empty files are not accepted")
            version = DocumentVersion(
                id=version_id,
                organization_id=identity.organization_id,
                project_id=project_id,
                document_id=document.id,
                version_number=1,
                filename=safe_filename,
                content_type=content_type,
                content_hash=f"sha256:{digest.hexdigest()}",
                object_key=object_key,
            )
            self._catalog.add(document, version)
        except Exception:
            self._catalog.remove(document.id, version_id)
            await self._objects.delete(key=object_key)
            raise
        return UploadResult(document=document, version=version.model_copy(deep=True))
