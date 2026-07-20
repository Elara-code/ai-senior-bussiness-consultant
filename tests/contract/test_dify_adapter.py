import httpx
import pytest

from consultant.adapters.workflows.dify import DifyWorkflowRunner
from consultant.domain.common import ExternalServiceFailure
from consultant.ports.workflow import WorkflowRef


@pytest.mark.asyncio
async def test_dify_adapter_sends_versioned_input_and_idempotency() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(
            200, json={"data": {"workflow_run_id": "run-1", "outputs": {"summary": "ok"}}}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await DifyWorkflowRunner(
            base_url="https://dify.example/v1", api_key="secret", client=client
        ).run(
            workflow=WorkflowRef("summary", "2026-07-20"),
            input={"text": "source"},
            idempotency_key="workflow-0001",
        )
    assert captured is not None
    assert captured.headers["Idempotency-Key"] == "workflow-0001"
    assert captured.headers["Authorization"] == "Bearer secret"
    assert b'"workflow_version":"2026-07-20"' in captured.content
    assert result.output == {"summary": "ok"}


@pytest.mark.asyncio
async def test_dify_adapter_maps_failures_without_leaking_response() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(500, text="secret"))
    ) as client:
        with pytest.raises(ExternalServiceFailure, match="temporarily"):
            await DifyWorkflowRunner(
                base_url="https://dify.example/v1", api_key="secret", client=client
            ).run(workflow=WorkflowRef("proposal", "v1"), input={}, idempotency_key="key-00001")
