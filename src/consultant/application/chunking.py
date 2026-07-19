import hashlib
from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

from consultant.application.parsing import ParsedBlock
from consultant.domain.documents import DocumentChunk


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    max_characters: int = 1800
    overlap_characters: int = 180

    def __post_init__(self) -> None:
        if self.max_characters < 100:
            raise ValueError("max_characters must be at least 100")
        if not 0 <= self.overlap_characters < self.max_characters:
            raise ValueError("overlap_characters must be smaller than max_characters")


def create_chunks(
    *,
    organization_id: UUID,
    project_id: UUID,
    document_version_id: UUID,
    blocks: list[ParsedBlock],
    config: ChunkingConfig | None = None,
) -> list[DocumentChunk]:
    config = config or ChunkingConfig()
    chunks: list[DocumentChunk] = []
    ordinal = 0
    for block in blocks:
        for text in _split(block.text, config):
            digest = hashlib.sha256(text.encode()).hexdigest()
            chunk_id = uuid5(
                NAMESPACE_URL,
                f"{document_version_id}:{ordinal}:sha256:{digest}",
            )
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    organization_id=organization_id,
                    project_id=project_id,
                    document_version_id=document_version_id,
                    ordinal=ordinal,
                    content=text,
                    content_hash=f"sha256:{digest}",
                    section=block.section,
                    page_start=block.page,
                    page_end=block.page,
                    token_count=max(1, (len(text) + 3) // 4),
                )
            )
            ordinal += 1
    return chunks


def _split(text: str, config: ChunkingConfig) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    if len(text) <= config.max_characters:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        hard_end = min(len(text), start + config.max_characters)
        end = hard_end
        if hard_end < len(text):
            preferred = max(text.rfind("。", start, hard_end), text.rfind(". ", start, hard_end))
            if preferred > start + config.max_characters // 2:
                end = preferred + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - config.overlap_characters)
    return chunks
