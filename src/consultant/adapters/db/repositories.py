from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from consultant.adapters.db.models import ProjectMemberRow, ProjectRow
from consultant.domain.projects import Project, ProjectStage


def scoped_project_statement(
    *, organization_id: UUID, project_id: UUID
) -> Select[tuple[ProjectRow]]:
    return select(ProjectRow).where(
        ProjectRow.organization_id == organization_id,
        ProjectRow.id == project_id,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, project: Project) -> None:
        self._session.add(
            ProjectRow(
                id=project.id,
                organization_id=project.organization_id,
                name=project.name,
                description=project.description,
                stage=project.stage.value,
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        )

    async def get(self, *, organization_id: UUID, project_id: UUID) -> Project | None:
        row = await self._session.scalar(
            scoped_project_statement(organization_id=organization_id, project_id=project_id)
        )
        return _to_domain(row) if row else None

    async def list_for_user(
        self, *, organization_id: UUID, user_id: UUID, limit: int = 50
    ) -> Sequence[Project]:
        statement = (
            select(ProjectRow)
            .join(
                ProjectMemberRow,
                (ProjectMemberRow.organization_id == ProjectRow.organization_id)
                & (ProjectMemberRow.project_id == ProjectRow.id),
            )
            .where(
                ProjectRow.organization_id == organization_id,
                ProjectMemberRow.organization_id == organization_id,
                ProjectMemberRow.user_id == user_id,
            )
            .order_by(ProjectRow.updated_at.desc())
            .limit(limit)
        )
        rows = (await self._session.scalars(statement)).all()
        return [_to_domain(row) for row in rows]


def _to_domain(row: ProjectRow) -> Project:
    return Project(
        id=row.id,
        organization_id=row.organization_id,
        name=row.name,
        description=row.description,
        stage=ProjectStage(row.stage),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
