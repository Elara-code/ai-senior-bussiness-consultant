from collections.abc import AsyncIterator
from uuid import UUID

from consultant.application.chunking import ChunkingConfig, create_chunks
from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.parsing import parse_document
from consultant.domain.documents import DocumentChunk, DocumentStatus
from consultant.ports.embeddings import EmbeddingProvider
from consultant.ports.object_store import ObjectStore


class DocumentPipeline:
    def __init__(
        self,
        *,
        catalog: InMemoryDocumentCatalog,
        object_store: ObjectStore,
        embeddings: EmbeddingProvider,
        chunking: ChunkingConfig | None = None,
    ) -> None:
        self._catalog = catalog
        self._objects = object_store
        self._embeddings = embeddings
        self._chunking = chunking or ChunkingConfig()

    async def process(self, version_id: UUID) -> list[DocumentChunk]:
        version = self._catalog.get_version(version_id)
        try:
            version.transition_to(DocumentStatus.PARSING)
            payload = await _read_all(self._objects.get_stream(key=version.object_key))
            blocks = parse_document(payload=payload, content_type=version.content_type)
            chunks = create_chunks(
                organization_id=version.organization_id,
                project_id=version.project_id,
                document_version_id=version.id,
                blocks=blocks,
                config=self._chunking,
            )
            if not chunks:
                raise ValueError("Document contains no indexable text")
            version.transition_to(DocumentStatus.EMBEDDING)
            vectors = await self._embeddings.embed_documents([chunk.content for chunk in chunks])
            if len(vectors) != len(chunks):
                raise ValueError("Embedding provider returned an unexpected vector count")
            for chunk, vector in zip(chunks, vectors, strict=True):
                if len(vector) != self._embeddings.dimensions:
                    raise ValueError("Embedding provider returned an unexpected dimension")
                chunk.embedding = vector
            self._catalog.add_chunks(chunks)
            version.transition_to(DocumentStatus.READY)
            return [chunk.model_copy(deep=True) for chunk in chunks]
        except Exception as error:
            if version.status != DocumentStatus.FAILED:
                version.transition_to(DocumentStatus.FAILED, failure_code=_failure_code(error))
            raise


async def _read_all(stream: AsyncIterator[bytes]) -> bytes:
    return b"".join([part async for part in stream])


def _failure_code(error: Exception) -> str:
    if isinstance(error, ValueError):
        return "INVALID_DOCUMENT"
    return "PROCESSING_FAILED"
