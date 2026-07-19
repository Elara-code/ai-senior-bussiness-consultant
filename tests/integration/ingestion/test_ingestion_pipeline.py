from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from consultant.adapters.llm.fake_embeddings import FakeEmbeddingProvider
from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.application.ingestion import DocumentIngestionService, InMemoryDocumentCatalog
from consultant.application.pipeline import DocumentPipeline
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.documents import DocumentStatus


async def _stream(payload: bytes) -> AsyncIterator[bytes]:
    yield payload


@pytest.mark.asyncio
async def test_pipeline_moves_document_to_ready_with_embedded_chunks() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    catalog = InMemoryDocumentCatalog()
    objects = InMemoryObjectStore()
    uploaded = await DocumentIngestionService(
        project_store=projects,
        catalog=catalog,
        object_store=objects,
        max_upload_bytes=1024,
    ).upload(
        identity=identity,
        project_id=project.id,
        filename="interview.md",
        content_type="text/markdown",
        stream=_stream(b"# Current Process\n\nReports are assembled manually."),
    )

    chunks = await DocumentPipeline(
        catalog=catalog,
        object_store=objects,
        embeddings=FakeEmbeddingProvider(dimensions=8),
    ).process(uploaded.version.id)

    assert catalog.get_version(uploaded.version.id).status == DocumentStatus.READY
    assert len(chunks) == 1
    assert len(chunks[0].embedding or []) == 8


@pytest.mark.asyncio
async def test_pipeline_records_public_failure_code() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    catalog = InMemoryDocumentCatalog()
    objects = InMemoryObjectStore()
    uploaded = await DocumentIngestionService(
        project_store=projects,
        catalog=catalog,
        object_store=objects,
        max_upload_bytes=1024,
    ).upload(
        identity=identity,
        project_id=project.id,
        filename="empty.txt",
        content_type="text/plain",
        stream=_stream(b"   "),
    )

    with pytest.raises(ValueError, match="no indexable text"):
        await DocumentPipeline(
            catalog=catalog,
            object_store=objects,
            embeddings=FakeEmbeddingProvider(),
        ).process(uploaded.version.id)

    version = catalog.get_version(uploaded.version.id)
    assert version.status == DocumentStatus.FAILED
    assert version.failure_code == "INVALID_DOCUMENT"
