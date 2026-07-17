from uuid import uuid4

import pytest
from pydantic import ValidationError

from consultant.domain.agent_runs import AgentKind, AgentRun, AgentRunStatus
from consultant.domain.common import InvalidStateTransition
from consultant.domain.documents import DocumentStatus, DocumentVersion
from consultant.domain.projects import Project, ProjectStage
from consultant.domain.retrieval import EvidenceRef


def test_project_rejects_skipping_business_stages() -> None:
    project = Project(organization_id=uuid4(), name="Customer AI program")

    with pytest.raises(InvalidStateTransition):
        project.transition_to(ProjectStage.PROPOSAL)


def test_completed_run_cannot_return_to_running() -> None:
    run = AgentRun(
        organization_id=uuid4(),
        project_id=uuid4(),
        actor_id=uuid4(),
        agent_kind=AgentKind.REQUIREMENT_ANALYSIS,
        objective="Create requirement baseline",
        idempotency_key="request-0001",
        status=AgentRunStatus.COMPLETED,
    )

    with pytest.raises(InvalidStateTransition):
        run.transition_to(AgentRunStatus.RUNNING)


def test_failed_document_requires_public_failure_code() -> None:
    version = DocumentVersion(
        organization_id=uuid4(),
        project_id=uuid4(),
        document_id=uuid4(),
        version_number=1,
        filename="interview.md",
        content_type="text/markdown",
        content_hash=f"sha256:{'a' * 64}",
        object_key="org/project/document/1",
    )

    with pytest.raises(ValueError, match="failure_code"):
        version.transition_to(DocumentStatus.FAILED)


def test_evidence_rejects_reversed_page_range() -> None:
    with pytest.raises(ValidationError, match="page_end"):
        EvidenceRef(
            id="CIT-001",
            organization_id=uuid4(),
            project_id=uuid4(),
            document_id=uuid4(),
            document_version_id=uuid4(),
            chunk_id=uuid4(),
            document_title="Interview",
            page_start=5,
            page_end=4,
            quote="The current report is prepared manually.",
            content_hash=f"sha256:{'b' * 64}",
        )
