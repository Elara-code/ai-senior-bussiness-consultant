from uuid import uuid4

import pytest

from consultant.adapters.llm.fake_embeddings import FakeEmbeddingProvider
from consultant.adapters.retrieval.fake_reranker import TokenOverlapReranker
from consultant.application.ingestion import InMemoryDocumentCatalog
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.application.retrieval import RetrievalService
from consultant.domain.common import NotFound


@pytest.mark.asyncio
async def test_retrieval_rejects_non_member_before_searching_chunks() -> None:
    organization_id = uuid4()
    owner = Identity(organization_id=organization_id, user_id=uuid4(), display_name="Owner")
    outsider = Identity(
        organization_id=organization_id, user_id=uuid4(), display_name="Outsider"
    )
    projects = InMemoryProjectStore()
    project = projects.create(identity=owner, name="Secret")

    with pytest.raises(NotFound):
        await RetrievalService(
            projects=projects,
            catalog=InMemoryDocumentCatalog(),
            embeddings=FakeEmbeddingProvider(),
            reranker=TokenOverlapReranker(),
        ).search(identity=outsider, project_id=project.id, query="secret")
