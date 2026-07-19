import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from consultant.adapters.retrieval.rrf import reciprocal_rank_fusion
from consultant.domain.documents import DocumentChunk


@dataclass(frozen=True, slots=True)
class RankedChunk:
    chunk: DocumentChunk
    fusion_score: float


def hybrid_candidates(
    *,
    query: str,
    query_vector: Sequence[float],
    chunks: Sequence[DocumentChunk],
    candidate_limit: int,
) -> list[RankedChunk]:
    if candidate_limit <= 0:
        raise ValueError("candidate_limit must be positive")
    vector_ranking = [
        chunk.id
        for chunk in sorted(
            chunks,
            key=lambda item: (-_cosine(query_vector, item.embedding or []), str(item.id)),
        )
        if chunk.embedding is not None
    ][:candidate_limit]
    keyword_ranking = [
        chunk.id
        for chunk in sorted(
            chunks,
            key=lambda item: (-_keyword_score(query, item.content), str(item.id)),
        )
        if _keyword_score(query, chunk.content) > 0
    ][:candidate_limit]
    by_id: dict[UUID, DocumentChunk] = {chunk.id: chunk for chunk in chunks}
    return [
        RankedChunk(chunk=by_id[item_id], fusion_score=score)
        for item_id, score in reciprocal_rank_fusion([vector_ranking, keyword_ranking])
        if isinstance(item_id, UUID)
    ][:candidate_limit]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    return sum(a * b for a, b in zip(left, right, strict=True)) / denominator if denominator else 0


def _keyword_score(query: str, document: str) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    document_tokens = _tokens(document)
    return len(query_tokens & document_tokens) / len(query_tokens)


def _tokens(text: str) -> set[str]:
    latin = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    han = [character for character in text if "\u4e00" <= character <= "\u9fff"]
    return set(latin + han)
