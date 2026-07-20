import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from consultant.adapters.db.base import create_engine, create_session_factory
from consultant.adapters.db.repositories import SqlAlchemyProjectRepository
from consultant.domain.projects import Project

DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is not configured")


@pytest.mark.asyncio
async def test_vector_extension_and_required_tables_exist() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL)
    async with engine.connect() as connection:
        extension = await connection.scalar(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        tables = set(
            (
                await connection.scalars(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname = 'public' ORDER BY tablename"
                    )
                )
            ).all()
        )
    await engine.dispose()

    assert extension == "vector"
    assert {
        "projects",
        "document_chunks",
        "agent_runs",
        "citations",
        "requirement_baselines",
        "approvals",
        "business_object_dependencies",
    } <= tables


@pytest.mark.asyncio
async def test_project_repository_never_crosses_organization_scope() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL)
    factory = create_session_factory(engine)
    organization_a = uuid4()
    organization_b = uuid4()
    shared_project_id = uuid4()

    async with factory() as session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO organizations (id, name) VALUES (:a, 'A'), (:b, 'B')"
                ),
                {"a": organization_a, "b": organization_b},
            )
            project = Project(
                id=shared_project_id,
                organization_id=organization_a,
                name="Project A",
            )
            repository = SqlAlchemyProjectRepository(session)
            await repository.add(project)

    async with factory() as session:
        repository = SqlAlchemyProjectRepository(session)
        allowed = await repository.get(
            organization_id=organization_a, project_id=shared_project_id
        )
        forbidden = await repository.get(
            organization_id=organization_b, project_id=shared_project_id
        )

    async with factory() as session:
        async with session.begin():
            await session.execute(
                text("DELETE FROM projects WHERE id = :project_id"),
                {"project_id": shared_project_id},
            )
            await session.execute(
                text("DELETE FROM organizations WHERE id IN (:a, :b)"),
                {"a": organization_a, "b": organization_b},
            )
    await engine.dispose()

    assert allowed is not None
    assert allowed.name == "Project A"
    assert forbidden is None
