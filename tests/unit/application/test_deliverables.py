from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from consultant.adapters.llm.fake_embeddings import FakeEmbeddingProvider
from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.application.deliverables import (
    CitationInput,
    DeliverableService,
    InMemoryDeliverableStore,
)
from consultant.application.ingestion import DocumentIngestionService, InMemoryDocumentCatalog
from consultant.application.pipeline import DocumentPipeline
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.deliverables import DeliverableKind


async def _stream(payload: bytes) -> AsyncIterator[bytes]:
    yield payload


@pytest.mark.asyncio
async def test_revisions_are_immutable_and_source_change_marks_stale() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    documents = InMemoryDocumentCatalog()
    objects = InMemoryObjectStore()
    uploaded = await DocumentIngestionService(
        project_store=projects,
        catalog=documents,
        object_store=objects,
        max_upload_bytes=4096,
    ).upload(
        identity=identity,
        project_id=project.id,
        filename="interview.txt",
        content_type="text/plain",
        stream=_stream(b"Reports are assembled manually."),
    )
    chunks = await DocumentPipeline(
        catalog=documents,
        object_store=objects,
        embeddings=FakeEmbeddingProvider(),
    ).process(uploaded.version.id)
    store = InMemoryDeliverableStore()
    service = DeliverableService(projects=projects, documents=documents, store=store)

    deliverable, first, citations = service.create_revision(
        identity=identity,
        project_id=project.id,
        kind=DeliverableKind.REQUIREMENT_BASELINE,
        title="Requirements",
        payload={"version": 1},
        rendered_markdown="# Requirements",
        source_run_id=uuid4(),
        citations=[CitationInput(chunk_id=chunks[0].id, quote="Reports are assembled manually.")],
    )
    _, second, _ = service.create_revision(
        identity=identity,
        project_id=project.id,
        deliverable_id=deliverable.id,
        kind=DeliverableKind.REQUIREMENT_BASELINE,
        title="Requirements",
        payload={"version": 2},
        rendered_markdown="# Requirements v2",
        source_run_id=uuid4(),
        citations=[CitationInput(chunk_id=chunks[0].id, quote="Reports are assembled manually.")],
    )
    affected = service.mark_stale_for_document_version(uploaded.version.id)

    assert first.version_number == 1
    assert first.payload == {"version": 1}
    assert second.version_number == 2
    assert citations[0].document_version_id == uploaded.version.id
    assert deliverable.id in affected
    assert store.deliverables[deliverable.id].stale is True
