from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from consultant.domain.common import Conflict, Forbidden, NotFound, new_id
from consultant.domain.projects import Project, ProjectRole, ProjectStage


@dataclass(frozen=True, slots=True)
class Identity:
    organization_id: UUID
    user_id: UUID
    display_name: str


@dataclass(frozen=True, slots=True)
class ProjectMember:
    id: UUID
    organization_id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectRole


class InMemoryProjectStore:
    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}
        self._members: dict[tuple[UUID, UUID], ProjectMember] = {}

    def create(self, *, identity: Identity, name: str, description: str = "") -> Project:
        project = Project(
            organization_id=identity.organization_id,
            name=name,
            description=description,
        )
        self._projects[project.id] = project
        self._members[(project.id, identity.user_id)] = ProjectMember(
            id=new_id(),
            organization_id=identity.organization_id,
            project_id=project.id,
            user_id=identity.user_id,
            role=ProjectRole.OWNER,
        )
        return project.model_copy(deep=True)

    def get_visible(self, *, identity: Identity, project_id: UUID) -> Project:
        project = self._projects.get(project_id)
        member = self._members.get((project_id, identity.user_id))
        if project is None or project.organization_id != identity.organization_id or member is None:
            raise NotFound("Project not found")
        return project.model_copy(deep=True)

    def list_visible(self, *, identity: Identity, limit: int = 50) -> Sequence[Project]:
        visible = [
            project.model_copy(deep=True)
            for project in self._projects.values()
            if project.organization_id == identity.organization_id
            and (project.id, identity.user_id) in self._members
        ]
        return sorted(visible, key=lambda project: project.updated_at, reverse=True)[:limit]

    def update_stage(
        self, *, identity: Identity, project_id: UUID, stage: ProjectStage
    ) -> Project:
        project = self._require_project(identity=identity, project_id=project_id)
        role = self._members[(project_id, identity.user_id)].role
        if role == ProjectRole.VIEWER:
            raise Forbidden("Viewers cannot update projects")
        project.transition_to(stage)
        return project.model_copy(deep=True)

    def add_member(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMember:
        project = self._require_project(identity=identity, project_id=project_id)
        actor = self._members[(project_id, identity.user_id)]
        if actor.role != ProjectRole.OWNER:
            raise Forbidden("Only project owners can manage members")
        key = (project_id, user_id)
        if key in self._members:
            raise Conflict("User is already a project member")
        member = ProjectMember(
            id=new_id(),
            organization_id=project.organization_id,
            project_id=project_id,
            user_id=user_id,
            role=role,
        )
        self._members[key] = member
        return member

    def role_for(self, *, identity: Identity, project_id: UUID) -> ProjectRole:
        self._require_project(identity=identity, project_id=project_id)
        return self._members[(project_id, identity.user_id)].role

    def _require_project(self, *, identity: Identity, project_id: UUID) -> Project:
        project = self._projects.get(project_id)
        member = self._members.get((project_id, identity.user_id))
        if project is None or project.organization_id != identity.organization_id or member is None:
            raise NotFound("Project not found")
        return project
