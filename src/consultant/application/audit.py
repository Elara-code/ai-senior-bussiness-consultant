from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from consultant.domain.common import new_id, utc_now


@dataclass(frozen=True, slots=True)
class AuditEvent:
    id: UUID
    action: str
    resource_type: str
    resource_id: str | None
    request_id: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=utc_now)


class InMemoryAuditLog:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(
        self,
        *,
        action: str,
        resource_type: str,
        request_id: str,
        outcome: str,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=new_id(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            outcome=outcome,
            metadata=metadata or {},
        )
        self.events.append(event)
        return event
