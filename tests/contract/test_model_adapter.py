import json

import httpx
import pytest

from consultant.adapters.llm.openai_compatible import OpenAICompatibleModel
from consultant.agents.schemas import RequirementAnalysisOutput
from consultant.ports.model import ModelMessage


@pytest.mark.asyncio
async def test_openai_compatible_adapter_sends_schema_and_parses_usage() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["response_format"]["type"] == "json_schema"
        return httpx.Response(
            200,
            headers={"x-request-id": "req-1"},
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "Summary",
                                    "claims": [],
                                    "requirements": [],
                                    "information_gaps": [],
                                    "interview_questions": [],
                                }
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await OpenAICompatibleModel(
            client=client,
            base_url="https://model.test/v1",
            api_key="secret",
            model="test-model",
            max_retries=0,
        ).generate(
            messages=[ModelMessage(role="user", content="Analyze")],
            output_schema=RequirementAnalysisOutput,
        )

    assert result.request_id == "req-1"
    assert result.usage.total_tokens == 15
