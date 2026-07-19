from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from consultant.adapters.llm.fake_embeddings import FakeEmbeddingProvider
from consultant.adapters.retrieval.fake_reranker import TokenOverlapReranker
from consultant.adapters.storage.memory import InMemoryObjectStore
from consultant.application.ingestion import DocumentIngestionService, InMemoryDocumentCatalog
from consultant.application.pipeline import DocumentPipeline
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.application.retrieval import RetrievalService


async def _stream(payload: bytes) -> AsyncIterator[bytes]:
    yield payload


@pytest.mark.asyncio
async def test_hybrid_search_returns_ready_project_evidence() -> None:
    identity = Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    catalog = InMemoryDocumentCatalog()
    objects = InMemoryObjectStore()
    embeddings = FakeEmbeddingProvider(dimensions=16)
    uploaded = await DocumentIngestionService(
        project_store=projects,
        catalog=catalog,
        object_store=objects,
        max_upload_bytes=4096,
    ).upload(
        identity=identity,
        project_id=project.id,
        filename="interview.md",
        content_type="text/markdown",
        stream=_stream("# 现状\n\n每周经营报告由三名员工手工汇总。".encode()),
    )
    await DocumentPipeline(
        catalog=catalog,
        object_store=objects,
        embeddings=embeddings,
    ).process(uploaded.version.id)

    hits = await RetrievalService(
        projects=projects,
        catalog=catalog,
        embeddings=embeddings,
        reranker=TokenOverlapReranker(),
    ).search(identity=identity, project_id=project.id, query="经营报告如何汇总？")

    assert hits
    assert hits[0].document_title == "interview.md"
    assert "手工汇总" in hits[0].content
