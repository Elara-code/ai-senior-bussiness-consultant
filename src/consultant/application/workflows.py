import hashlib
import json
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any
from uuid import UUID

from consultant.domain.business_loop import WorkflowExecution, WorkflowStatus
from consultant.domain.common import ExternalServiceFailure
from consultant.ports.workflow import WorkflowRef, WorkflowResult, WorkflowRunner

LocalFallback = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class InMemoryWorkflowExecutionStore:
    def __init__(self) -> None:
        self.executions: dict[UUID, WorkflowExecution] = {}

    def save(self, execution: WorkflowExecution) -> None:
        self.executions[execution.id] = execution.model_copy(deep=True)


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


async def execute_governed_workflow(
    *,
    organization_id: UUID,
    project_id: UUID,
    runner: WorkflowRunner,
    workflow: WorkflowRef,
    input: dict[str, Any],
    idempotency_key: str,
    purpose: str,
    store: InMemoryWorkflowExecutionStore,
    local_fallback: LocalFallback | None = None,
) -> WorkflowResult:
    digest = hashlib.sha256(
        json.dumps(input, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    execution = WorkflowExecution(
        organization_id=organization_id,
        project_id=project_id,
        workflow_id=workflow.workflow_id,
        workflow_version=workflow.version,
        idempotency_key=idempotency_key,
        input_digest=f"sha256:{digest}",
        status=WorkflowStatus.RUNNING,
    )
    store.save(execution)
    started = perf_counter()
    try:
        result = await run_with_policy(
            runner=runner,
            workflow=workflow,
            input=input,
            idempotency_key=idempotency_key,
            purpose=purpose,
            local_fallback=local_fallback,
        )
        execution.output = result.output
        execution.status = WorkflowStatus.COMPLETED
        return result
    except ExternalServiceFailure:
        execution.status = WorkflowStatus.FAILED
        execution.error_code = "WORKFLOW_UNAVAILABLE"
        raise
    finally:
        execution.duration_ms = max(0, int((perf_counter() - started) * 1000))
        store.save(execution)
