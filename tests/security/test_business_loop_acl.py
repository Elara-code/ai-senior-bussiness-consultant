from uuid import uuid4

import pytest

from consultant.application.business_loop import (
    BusinessLoopService,
    InMemoryBusinessObjectRepository,
)
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.business_loop import BusinessObjectKind
from consultant.domain.common import NotFound


@pytest.mark.asyncio
async def test_business_objects_never_cross_project_scope() -> None:
    identity = Identity(uuid4(), uuid4(), "Owner")
    projects = InMemoryProjectStore()
    project_a = projects.create(identity=identity, name="A")
    project_b = projects.create(identity=identity, name="B")
    service = BusinessLoopService(
        projects=projects, repository=InMemoryBusinessObjectRepository()
    )
    item = await service.create(
        identity=identity,
        project_id=project_a.id,
        kind=BusinessObjectKind.PROPOSAL,
        title="A proposal",
        payload={},
    )

    with pytest.raises(NotFound):
        await service.get(identity=identity, project_id=project_b.id, item_id=item.id)
