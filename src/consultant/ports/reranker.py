from collections.abc import Sequence
from typing import Protocol


class Reranker(Protocol):
    async def rerank(
        self, *, query: str, documents: Sequence[str]
    ) -> list[float]: ...
