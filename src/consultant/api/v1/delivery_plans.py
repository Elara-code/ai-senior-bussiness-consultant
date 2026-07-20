from consultant.api.v1.business_objects import build_business_object_router
from consultant.domain.business_loop import BusinessObjectKind

router = build_business_object_router(
    kind=BusinessObjectKind.DELIVERY_PLAN,
    path="delivery-plans",
    tag="delivery-plans",
)
