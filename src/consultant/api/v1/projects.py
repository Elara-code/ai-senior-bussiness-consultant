from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from consultant.api.dependencies import CurrentIdentity, ProjectStore
from consultant.domain.projects import Project, ProjectRole, ProjectStage

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)


class UpdateProjectRequest(BaseModel):
    stage: ProjectStage


class AddMemberRequest(BaseModel):
    user_id: UUID
    role: ProjectRole


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectRole


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest, identity: CurrentIdentity, store: ProjectStore
) -> Project:
    return store.create(identity=identity, name=request.name, description=request.description)


@router.get("", response_model=list[Project])
def list_projects(
    identity: CurrentIdentity,
    store: ProjectStore,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[Project]:
    return list(store.list_visible(identity=identity, limit=limit))


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: UUID, identity: CurrentIdentity, store: ProjectStore) -> Project:
    return store.get_visible(identity=identity, project_id=project_id)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    identity: CurrentIdentity,
    store: ProjectStore,
) -> Project:
    return store.update_stage(identity=identity, project_id=project_id, stage=request.stage)


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_project_member(
    project_id: UUID,
    request: AddMemberRequest,
    identity: CurrentIdentity,
    store: ProjectStore,
) -> ProjectMemberResponse:
    member = store.add_member(
        identity=identity,
        project_id=project_id,
        user_id=request.user_id,
        role=request.role,
    )
    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
    )
