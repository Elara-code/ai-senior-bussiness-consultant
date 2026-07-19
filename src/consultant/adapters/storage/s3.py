from collections.abc import AsyncIterator
from typing import Any, Protocol


class AsyncS3Client(Protocol):
    async def put_object(self, **kwargs: Any) -> Any: ...

    async def get_object(self, **kwargs: Any) -> dict[str, Any]: ...

    async def delete_object(self, **kwargs: Any) -> Any: ...


class S3ObjectStore:
    """Adapter for an aioboto3-compatible client.

    The application only depends on ObjectStore; importing a concrete AWS SDK is
    deferred until deployment wiring so unit tests stay offline and deterministic.
    """

    def __init__(self, *, client: AsyncS3Client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def put_stream(
        self, *, key: str, stream: AsyncIterator[bytes], content_type: str
    ) -> None:
        body = b"".join([part async for part in stream])
        await self._client.put_object(
            Bucket=self._bucket, Key=key, Body=body, ContentType=content_type
        )

    async def get_stream(self, *, key: str) -> AsyncIterator[bytes]:
        response = await self._client.get_object(Bucket=self._bucket, Key=key)
        body = response["Body"]
        while chunk := await body.read(1024 * 1024):
            yield chunk

    async def delete(self, *, key: str) -> None:
        await self._client.delete_object(Bucket=self._bucket, Key=key)
