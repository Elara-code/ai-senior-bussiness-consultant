from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class EvidenceRef(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    organization_id: UUID
    project_id: UUID
    document_id: UUID
    document_version_id: UUID
    chunk_id: UUID
    document_title: str
    section: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    quote: str = Field(min_length=1, max_length=1200)
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    score: float | None = None

    @model_validator(mode="after")
    def validate_page_range(self) -> "EvidenceRef":
        if self.page_start is None and self.page_end is not None:
            raise ValueError("page_start is required when page_end is provided")
        if (
            self.page_start is not None
            and self.page_end is not None
            and self.page_end < self.page_start
        ):
            raise ValueError("page_end must be greater than or equal to page_start")
        return self
