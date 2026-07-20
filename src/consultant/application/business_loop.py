from collections.abc import Sequence
from uuid import UUID

from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.business_loop import (
    BusinessObjectKind,
    EvidenceStatement,
    VersionedBusinessObject,
)
from consultant.domain.common import Forbidden, NotFound
from consultant.domain.projects import ProjectRole
from consultant.ports.business_loop import BusinessObjectRepository


class InMemoryBusinessObjectRepository:
    def __init__(self) -> None:
        self.history: dict[UUID, list[VersionedBusinessObject]] = {}
        self.dependencies: dict[UUID, set[UUID]] = {}

    async def add(self, item: VersionedBusinessObject) -> None:
        if item.id in self.history:
            await self.mark_stale(
                organization_id=item.organization_id,
                project_id=item.project_id,
                item_ids=self.dependencies.get(item.id, set()),
            )
        self.history.setdefault(item.id, []).append(item.model_copy(deep=True))

    async def save_state(self, item: VersionedBusinessObject) -> None:
        versions = self.history.get(item.id, [])
        if not versions or versions[-1].version != item.version:
            raise NotFound("Business object version not found")
        versions[-1] = item.model_copy(deep=True)

    async def get_latest(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        item_id: UUID,
    ) -> VersionedBusinessObject | None:
        versions = self.history.get(item_id, [])
        if not versions:
            return None
        item = versions[-1]
        if item.organization_id != organization_id or item.project_id != project_id:
            return None
        return item.model_copy(deep=True)

    async def list_latest(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        kind: BusinessObjectKind | None = None,
    ) -> Sequence[VersionedBusinessObject]:
        items = [
            versions[-1].model_copy(deep=True)
            for versions in self.history.values()
            if versions
            and versions[-1].organization_id == organization_id
            and versions[-1].project_id == project_id
            and (kind is None or versions[-1].kind == kind)
        ]
        return sorted(items, key=lambda item: item.updated_at, reverse=True)

    async def mark_stale(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        item_ids: set[UUID],
    ) -> None:
        for item_id in item_ids:
            item = await self.get_latest(
                organization_id=organization_id,
                project_id=project_id,
                item_id=item_id,
            )
            if item is not None:
                item.stale = True
                self.history[item_id][-1] = item

    async def link_dependencies(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        upstream_ids: set[UUID],
        downstream_id: UUID,
    ) -> None:
        downstream = await self.get_latest(
            organization_id=organization_id,
            project_id=project_id,
            item_id=downstream_id,
        )
        if downstream is None:
            raise NotFound("Downstream business object not found")
        for upstream_id in upstream_ids:
            upstream = await self.get_latest(
                organization_id=organization_id,
                project_id=project_id,
                item_id=upstream_id,
            )
            if upstream is None:
                raise NotFound("Upstream business object not found")
            self.dependencies.setdefault(upstream_id, set()).add(downstream_id)


class BusinessLoopService:
    def __init__(
        self,
        *,
        projects: InMemoryProjectStore,
        repository: BusinessObjectRepository,
    ) -> None:
        self._projects = projects
        self._repository = repository

    async def create(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        kind: BusinessObjectKind,
        title: str,
        payload: dict[str, object],
        statements: list[EvidenceStatement] | None = None,
    ) -> VersionedBusinessObject:
        self._require_editor(identity=identity, project_id=project_id)
        item = VersionedBusinessObject(
            organization_id=identity.organization_id,
            project_id=project_id,
            kind=kind,
            title=title,
            payload=payload,
            statements=statements or [],
        )
        await self._repository.add(item)
        return item.model_copy(deep=True)

    async def revise(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        item_id: UUID,
        expected_version: int,
        payload: dict[str, object],
        title: str | None = None,
        statements: list[EvidenceStatement] | None = None,
    ) -> VersionedBusinessObject:
        self._require_editor(identity=identity, project_id=project_id)
        item = await self._require_visible(
            identity=identity, project_id=project_id, item_id=item_id
        )
        revised = item.revise(
            payload=payload,
            expected_version=expected_version,
            title=title,
            statements=statements,
        )
        await self._repository.add(revised)
        return revised.model_copy(deep=True)

    async def get(
        self, *, identity: Identity, project_id: UUID, item_id: UUID
    ) -> VersionedBusinessObject:
        self._projects.get_visible(identity=identity, project_id=project_id)
        return await self._require_visible(
            identity=identity, project_id=project_id, item_id=item_id
        )

    async def list(
        self,
        *,
        identity: Identity,
        project_id: UUID,
        kind: BusinessObjectKind | None = None,
    ) -> Sequence[VersionedBusinessObject]:
        self._projects.get_visible(identity=identity, project_id=project_id)
        return await self._repository.list_latest(
            organization_id=identity.organization_id,
            project_id=project_id,
            kind=kind,
        )

    async def _require_visible(
        self, *, identity: Identity, project_id: UUID, item_id: UUID
    ) -> VersionedBusinessObject:
        item = await self._repository.get_latest(
            organization_id=identity.organization_id,
            project_id=project_id,
            item_id=item_id,
        )
        if item is None:
            raise NotFound("Business object not found")
        return item

    def _require_editor(self, *, identity: Identity, project_id: UUID) -> None:
        role = self._projects.role_for(identity=identity, project_id=project_id)
        if role == ProjectRole.VIEWER:
            raise Forbidden("Viewers cannot modify business objects")
