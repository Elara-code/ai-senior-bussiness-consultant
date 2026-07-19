from uuid import uuid4

import pytest

from consultant.application.projects import Identity
from consultant.application.retrieval import RetrievalHit


@pytest.fixture
def identity() -> Identity:
    return Identity(organization_id=uuid4(), user_id=uuid4(), display_name="Consultant")


@pytest.fixture
def evidence_hit() -> RetrievalHit:
    return RetrievalHit(
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_version_id=uuid4(),
        document_title="访谈纪要",
        content="每周经营报告由三名员工手工汇总。",
        section="现状",
        page_start=2,
        page_end=2,
        content_hash=f"sha256:{'a' * 64}",
        score=1.0,
    )
