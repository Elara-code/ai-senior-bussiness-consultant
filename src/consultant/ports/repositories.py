from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from consultant.domain.projects import Project


class ProjectRepository(Protocol):
    async def add(self, project: Project) -> None: ...

    async def get(self, *, organization_id: UUID, project_id: UUID) -> Project | None: ...

    async def list_for_user(
        self, *, organization_id: UUID, user_id: UUID, limit: int = 50
    ) -> Sequence[Project]: ...
