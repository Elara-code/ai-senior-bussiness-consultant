from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from consultant.domain.common import InvalidStateTransition, new_id, utc_now


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class SourceDocument(BaseModel):
    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    title: str = Field(min_length=1, max_length=255)
    created_at: datetime = Field(default_factory=utc_now)


_DOCUMENT_TRANSITIONS: dict[DocumentStatus, frozenset[DocumentStatus]] = {
    DocumentStatus.PENDING: frozenset({DocumentStatus.PARSING, DocumentStatus.FAILED}),
    DocumentStatus.PARSING: frozenset({DocumentStatus.EMBEDDING, DocumentStatus.FAILED}),
    DocumentStatus.EMBEDDING: frozenset({DocumentStatus.READY, DocumentStatus.FAILED}),
    DocumentStatus.READY: frozenset(),
    DocumentStatus.FAILED: frozenset({DocumentStatus.PENDING}),
}


class DocumentVersion(BaseModel):
    id: UUID = Field(default_factory=new_id)
    organization_id: UUID
    project_id: UUID
    document_id: UUID
    version_number: int = Field(ge=1)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=127)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    object_key: str = Field(min_length=1, max_length=1024)
    status: DocumentStatus = DocumentStatus.PENDING
    failure_code: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    def transition_to(self, target: DocumentStatus, *, failure_code: str | None = None) -> None:
        if target == self.status:
            return
        if target not in _DOCUMENT_TRANSITIONS[self.status]:
            raise InvalidStateTransition(f"Cannot move document from {self.status} to {target}")
        if target == DocumentStatus.FAILED and not failure_code:
            raise ValueError("failure_code is required when a document fails")
        self.status = target
        self.failure_code = failure_code if target == DocumentStatus.FAILED else None


class DocumentChunk(BaseModel):
    id: UUID
    organization_id: UUID
    project_id: UUID
    document_version_id: UUID
    ordinal: int = Field(ge=0)
    content: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    section: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    token_count: int = Field(gt=0)
    embedding: list[float] | None = None
