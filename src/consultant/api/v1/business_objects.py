from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Response, status
from pydantic import BaseModel, Field

from consultant.api.dependencies import BusinessObjects, CurrentIdentity, ProjectStore
from consultant.application.business_loop import BusinessLoopService
from consultant.domain.business_loop import (
    BusinessObjectKind,
    EvidenceStatement,
    VersionedBusinessObject,
)
from consultant.domain.common import ValidationFailure


class CreateBusinessObjectRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]
    statements: list[EvidenceStatement] = Field(default_factory=list)


class ReviseBusinessObjectRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    payload: dict[str, Any]
    statements: list[EvidenceStatement] | None = None


def build_business_object_router(
    *, kind: BusinessObjectKind, path: str, tag: str
) -> APIRouter:
    router = APIRouter(prefix=f"/projects/{{project_id}}/{path}", tags=[tag])

    @router.post("", response_model=VersionedBusinessObject, status_code=status.HTTP_201_CREATED)
    async def create_item(
        project_id: UUID,
        request: CreateBusinessObjectRequest,
        response: Response,
        identity: CurrentIdentity,
        projects: ProjectStore,
        repository: BusinessObjects,
    ) -> VersionedBusinessObject:
        item = await BusinessLoopService(projects=projects, repository=repository).create(
            identity=identity,
            project_id=project_id,
            kind=kind,
            title=request.title,
            payload=request.payload,
            statements=request.statements,
        )
        response.headers["ETag"] = _etag(item.version)
        return item

    @router.get("", response_model=list[VersionedBusinessObject])
    async def list_items(
        project_id: UUID,
        identity: CurrentIdentity,
        projects: ProjectStore,
        repository: BusinessObjects,
    ) -> list[VersionedBusinessObject]:
        items = await BusinessLoopService(projects=projects, repository=repository).list(
            identity=identity, project_id=project_id, kind=kind
        )
        return list(items)

    @router.get("/{item_id}", response_model=VersionedBusinessObject)
    async def get_item(
        project_id: UUID,
        item_id: UUID,
        response: Response,
        identity: CurrentIdentity,
        projects: ProjectStore,
        repository: BusinessObjects,
    ) -> VersionedBusinessObject:
        item = await BusinessLoopService(projects=projects, repository=repository).get(
            identity=identity, project_id=project_id, item_id=item_id
        )
        if item.kind != kind:
            from consultant.domain.common import NotFound

            raise NotFound("Business object not found")
        response.headers["ETag"] = _etag(item.version)
        return item

    @router.put("/{item_id}", response_model=VersionedBusinessObject)
    async def revise_item(
        project_id: UUID,
        item_id: UUID,
        request: ReviseBusinessObjectRequest,
        response: Response,
        identity: CurrentIdentity,
        projects: ProjectStore,
        repository: BusinessObjects,
        if_match: Annotated[str | None, Header()] = None,
    ) -> VersionedBusinessObject:
        expected_version = _parse_etag(if_match)
        current = await BusinessLoopService(projects=projects, repository=repository).get(
            identity=identity, project_id=project_id, item_id=item_id
        )
        if current.kind != kind:
            from consultant.domain.common import NotFound

            raise NotFound("Business object not found")
        item = await BusinessLoopService(projects=projects, repository=repository).revise(
            identity=identity,
            project_id=project_id,
            item_id=item_id,
            expected_version=expected_version,
            title=request.title,
            payload=request.payload,
            statements=request.statements,
        )
        response.headers["ETag"] = _etag(item.version)
        return item

    return router


def _etag(version: int) -> str:
    return f'"{version}"'


def _parse_etag(value: str | None) -> int:
    if value is None:
        raise ValidationFailure("If-Match header is required")
    normalized = value.removeprefix("W/").strip('"')
    try:
        version = int(normalized)
    except ValueError as error:
        raise ValidationFailure("If-Match must contain a numeric version") from error
    if version < 1:
        raise ValidationFailure("If-Match version must be positive")
    return version
