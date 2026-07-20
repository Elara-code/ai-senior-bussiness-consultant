from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class WorkflowRef:
    workflow_id: str
    version: str


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    output: dict[str, Any]
    execution_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowRunner(Protocol):
    async def run(
        self, *, workflow: WorkflowRef, input: dict[str, Any], idempotency_key: str
    ) -> WorkflowResult: ...
