from collections.abc import Awaitable, Callable, Sequence


class ProviderEmbeddingAdapter:
    """Provider-neutral embedding adapter with strict dimension validation."""

    def __init__(
        self,
        *,
        dimensions: int,
        embed_call: Callable[[Sequence[str]], Awaitable[list[list[float]]]],
    ) -> None:
        self._dimensions = dimensions
        self._embed_call = embed_call

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = await self._embed_call(texts)
        if len(vectors) != len(texts):
            raise ValueError("Embedding provider returned an unexpected vector count")
        if any(len(vector) != self.dimensions for vector in vectors):
            raise ValueError("Embedding provider returned an unexpected dimension")
        return vectors
