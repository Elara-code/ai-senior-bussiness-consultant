from uuid import uuid4

import pytest

from consultant.application.business_loop import (
    BusinessLoopService,
    InMemoryBusinessObjectRepository,
)
from consultant.application.projects import Identity, InMemoryProjectStore
from consultant.domain.business_loop import BusinessObjectKind
from consultant.domain.common import Conflict


@pytest.mark.asyncio
async def test_business_objects_keep_versions_and_reject_stale_writes() -> None:
    identity = Identity(uuid4(), uuid4(), "Owner")
    projects = InMemoryProjectStore()
    project = projects.create(identity=identity, name="Customer")
    repository = InMemoryBusinessObjectRepository()
    service = BusinessLoopService(projects=projects, repository=repository)

    created = await service.create(
        identity=identity,
        project_id=project.id,
        kind=BusinessObjectKind.REQUIREMENT_BASELINE,
        title="需求基线",
        payload={"goals": ["提高效率"]},
    )
    revised = await service.revise(
        identity=identity,
        project_id=project.id,
        item_id=created.id,
        expected_version=1,
        payload={"goals": ["提高效率", "降低成本"]},
    )

    assert revised.version == 2
    assert [item.version for item in repository.history[created.id]] == [1, 2]
    with pytest.raises(Conflict):
        await service.revise(
            identity=identity,
            project_id=project.id,
            item_id=created.id,
            expected_version=1,
            payload={},
        )
