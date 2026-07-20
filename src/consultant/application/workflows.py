from collections.abc import Awaitable, Callable
from typing import Any

from consultant.domain.common import ExternalServiceFailure
from consultant.ports.workflow import WorkflowRef, WorkflowResult, WorkflowRunner

LocalFallback = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


async def run_with_policy(
    *,
    runner: WorkflowRunner,
    workflow: WorkflowRef,
    input: dict[str, Any],
    idempotency_key: str,
    purpose: str,
    local_fallback: LocalFallback | None = None,
) -> WorkflowResult:
    try:
        return await runner.run(workflow=workflow, input=input, idempotency_key=idempotency_key)
    except ExternalServiceFailure:
        if purpose == "material_summary" and local_fallback is not None:
            return WorkflowResult(
                output=await local_fallback(input), metadata={"fallback": "local_agent"}
            )
        raise
