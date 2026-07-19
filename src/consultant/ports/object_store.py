from collections.abc import AsyncIterator
from typing import Protocol


class ObjectStore(Protocol):
    async def put_stream(
        self, *, key: str, stream: AsyncIterator[bytes], content_type: str
    ) -> None: ...

    def get_stream(self, *, key: str) -> AsyncIterator[bytes]: ...

    async def delete(self, *, key: str) -> None: ...
