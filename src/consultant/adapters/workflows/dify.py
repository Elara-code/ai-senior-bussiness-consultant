from typing import Any

import httpx

from consultant.domain.common import ExternalServiceFailure
from consultant.ports.workflow import WorkflowRef, WorkflowResult


class DifyWorkflowRunner:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 30,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = client

    async def run(
        self, *, workflow: WorkflowRef, input: dict[str, Any], idempotency_key: str
    ) -> WorkflowResult:
        payload = {
            "inputs": {"schema_version": "1.0", "workflow_version": workflow.version, **input},
            "response_mode": "blocking",
            "user": "ai-consultant-platform",
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Idempotency-Key": idempotency_key}
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.post(
                f"{self._base_url}/workflows/run", json=payload, headers=headers
            )
            response.raise_for_status()
            body = response.json()
            data = body.get("data", body)
            outputs = data.get("outputs")
            if not isinstance(outputs, dict):
                raise ExternalServiceFailure("Dify returned an invalid workflow output")
            execution_id = data.get("workflow_run_id") or body.get("workflow_run_id")
            return WorkflowResult(
                output=outputs,
                execution_id=str(execution_id) if execution_id else None,
                metadata={"workflow_id": workflow.workflow_id, "version": workflow.version},
            )
        except (httpx.HTTPError, ValueError) as error:
            raise ExternalServiceFailure("Dify workflow is temporarily unavailable") from error
        finally:
            if owns_client:
                await client.aclose()
