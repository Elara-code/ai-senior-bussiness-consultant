from typing import Any

from consultant.ports.workflow import WorkflowRef, WorkflowResult


class FakeWorkflowRunner:
    def __init__(self, output: dict[str, Any] | None = None) -> None:
        self.output = output or {"summary": "Fake workflow completed"}
        self.calls: list[tuple[WorkflowRef, dict[str, Any], str]] = []

    async def run(
        self, *, workflow: WorkflowRef, input: dict[str, Any], idempotency_key: str
    ) -> WorkflowResult:
        self.calls.append((workflow, input, idempotency_key))
        return WorkflowResult(output=self.output, execution_id=f"fake-{len(self.calls)}")
