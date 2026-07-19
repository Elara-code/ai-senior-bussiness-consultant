import hashlib
from collections.abc import Sequence


class FakeEmbeddingProvider:
    def __init__(self, dimensions: int = 16) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [((digest[index % len(digest)] / 255) * 2) - 1 for index in range(self.dimensions)]
