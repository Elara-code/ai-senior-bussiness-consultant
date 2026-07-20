from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from consultant.domain.business_loop import BusinessObjectKind, VersionedBusinessObject


class BusinessObjectRepository(Protocol):
    async def add(self, item: VersionedBusinessObject) -> None: ...

    async def save_state(self, item: VersionedBusinessObject) -> None: ...

    async def get_latest(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        item_id: UUID,
    ) -> VersionedBusinessObject | None: ...

    async def list_latest(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        kind: BusinessObjectKind | None = None,
    ) -> Sequence[VersionedBusinessObject]: ...

    async def mark_stale(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        item_ids: set[UUID],
    ) -> None: ...

    async def link_dependencies(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        upstream_ids: set[UUID],
        downstream_id: UUID,
    ) -> None: ...
