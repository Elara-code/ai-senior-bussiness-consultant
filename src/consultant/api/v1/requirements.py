from consultant.api.v1.business_objects import build_business_object_router
from consultant.domain.business_loop import BusinessObjectKind

router = build_business_object_router(
    kind=BusinessObjectKind.REQUIREMENT_BASELINE,
    path="requirements",
    tag="requirements",
)
