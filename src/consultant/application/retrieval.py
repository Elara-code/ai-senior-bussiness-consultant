from dataclasses import dataclass
from uuid import UUID

from consultant.adapters.retrieval.hybrid import hybrid_candidates
from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.documents import DocumentStatus
from consultant.ports.embeddings import EmbeddingProvider
from consultant.ports.reranker import Reranker


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    document_title: str
    content: str
    section: str | None
    page_start: int | None
    page_end: int | None
    content_hash: str
    score: float


class RetrievalService:
    def __init__(
        self,
        *,
        projects: InMemoryProjectStore,
        catalog: InMemoryDocumentCatalog,
        embeddings: EmbeddingProvider,
        reranker: Reranker,
    ) -> None:
        self._projects = projects
        self._catalog = catalog
        self._embeddings = embeddings
        self._reranker = reranker

    async def search(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        query: str,
        top_k: int = 8,
        candidate_limit: int = 30,
    ) -> list[RetrievalHit]:
        self._projects.get_visible(identity=identity, project_id=project_id)
        allowed_versions = {
            version.id: version
            for version in self._catalog.versions.values()
            if version.organization_id == identity.organization_id
            and version.project_id == project_id
            and version.status == DocumentStatus.READY
        }
        chunks = [
            chunk
            for chunk in self._catalog.chunks.values()
            if chunk.organization_id == identity.organization_id
            and chunk.project_id == project_id
            and chunk.document_version_id in allowed_versions
        ]
        query_vector = (await self._embeddings.embed_documents([query]))[0]
        candidates = hybrid_candidates(
            query=query,
            query_vector=query_vector,
            chunks=chunks,
            candidate_limit=candidate_limit,
        )
        if not candidates:
            return []
        rerank_scores = await self._reranker.rerank(
            query=query, documents=[item.chunk.content for item in candidates]
        )
        if len(rerank_scores) != len(candidates):
            raise ValueError("Reranker returned an unexpected score count")
        ranked = sorted(
            zip(candidates, rerank_scores, strict=True),
            key=lambda item: (-item[1], -item[0].fusion_score, str(item[0].chunk.id)),
        )[:top_k]
        hits: list[RetrievalHit] = []
        for candidate, score in ranked:
            version = allowed_versions[candidate.chunk.document_version_id]
            document = self._catalog.documents[version.document_id]
            hits.append(
                RetrievalHit(
                    chunk_id=candidate.chunk.id,
                    document_id=document.id,
                    document_version_id=version.id,
                    document_title=document.title,
                    content=candidate.chunk.content,
                    section=candidate.chunk.section,
                    page_start=candidate.chunk.page_start,
                    page_end=candidate.chunk.page_end,
                    content_hash=candidate.chunk.content_hash,
                    score=score,
                )
            )
        return hits
