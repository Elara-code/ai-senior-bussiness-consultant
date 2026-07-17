from uuid import uuid4

from sqlalchemy.dialects import postgresql

from consultant.adapters.db.base import Base
from consultant.adapters.db.repositories import scoped_project_statement


def test_initial_metadata_contains_required_tables() -> None:
    required = {
        "organizations",
        "users",
        "projects",
        "project_members",
        "source_documents",
        "document_versions",
        "document_chunks",
        "agent_runs",
        "run_events",
        "deliverables",
        "deliverable_revisions",
        "citations",
        "audit_logs",
    }

    assert required <= set(Base.metadata.tables)


def test_project_query_is_scoped_by_organization_and_project() -> None:
    organization_id = uuid4()
    project_id = uuid4()

    compiled = str(
        scoped_project_statement(
            organization_id=organization_id,
            project_id=project_id,
        ).compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
    )

    assert "projects.organization_id" in compiled
    assert str(organization_id) in compiled
    assert "projects.id" in compiled
    assert str(project_id) in compiled
