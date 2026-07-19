from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.application.ingestion import DocumentIngestionService, InMemoryDocumentCatalog
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.common import ValidationFailure


async def _stream(payload: bytes) -> AsyncIterator[bytes]:
    yield payload


@pytest.mark.asyncio
async def test_upload_hashes_sanitizes_and_stores_document() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    catalog = InMemoryDocumentCatalog()
    objects = InMemoryObjectStore()

    result = await DocumentIngestionService(
        project_store=projects,
        catalog=catalog,
        object_store=objects,
        max_upload_bytes=1024,
    ).upload(
        identity=identity,
        project_id=project.id,
        filename="../../interview.md",
        content_type="text/markdown",
        stream=_stream(b"manual reporting"),
    )

    assert result.version.filename == "interview.md"
    assert result.version.content_hash.startswith("sha256:")
    assert objects.objects[result.version.object_key] == b"manual reporting"


@pytest.mark.asyncio
async def test_oversized_upload_is_removed_from_object_store() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    objects = InMemoryObjectStore()

    with pytest.raises(ValidationFailure, match="upload limit"):
        await DocumentIngestionService(
            project_store=projects,
            catalog=InMemoryDocumentCatalog(),
            object_store=objects,
            max_upload_bytes=3,
        ).upload(
            identity=identity,
            project_id=project.id,
            filename="large.txt",
            content_type="text/plain",
            stream=_stream(b"too large"),
        )

    assert objects.objects == {}
