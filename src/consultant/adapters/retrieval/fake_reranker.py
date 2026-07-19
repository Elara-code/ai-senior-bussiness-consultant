import re
from collections.abc import Sequence


class TokenOverlapReranker:
    async def rerank(self, *, query: str, documents: Sequence[str]) -> list[float]:
        query_tokens = _tokens(query)
        return [
            len(query_tokens & _tokens(document)) / max(1, len(query_tokens))
            for document in documents
        ]


def _tokens(text: str) -> set[str]:
    latin = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    han = [character for character in text if "\u4e00" <= character <= "\u9fff"]
    return set(latin + han)
