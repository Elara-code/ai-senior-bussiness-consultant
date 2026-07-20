from typing import Any

import pytest

from consultant.application.workflows import run_with_policy
from consultant.domain.common import ExternalServiceFailure
from consultant.ports.workflow import WorkflowRef, WorkflowResult


class FailingRunner:
    async def run(self, **kwargs: Any) -> WorkflowResult:
        del kwargs
        raise ExternalServiceFailure("unavailable")


@pytest.mark.asyncio
async def test_material_summary_falls_back_but_proposal_does_not() -> None:
    async def fallback(input: dict[str, Any]) -> dict[str, Any]:
        return {"summary": input["text"]}

    result = await run_with_policy(
        runner=FailingRunner(),
        workflow=WorkflowRef("summary", "v1"),
        input={"text": "local"},
        idempotency_key="fallback-001",
        purpose="material_summary",
        local_fallback=fallback,
    )
    assert result.output == {"summary": "local"}
    with pytest.raises(ExternalServiceFailure):
        await run_with_policy(
            runner=FailingRunner(),
            workflow=WorkflowRef("proposal", "v1"),
            input={},
            idempotency_key="proposal-001",
            purpose="proposal",
        )
