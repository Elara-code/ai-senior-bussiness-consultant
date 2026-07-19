import asyncio
import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from consultant.domain.common import ExternalServiceFailure
from consultant.ports.model import ModelMessage, ModelResult, ModelUsage, StructuredOutput


class OpenAICompatibleModel:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 60,
        max_retries: int = 2,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    async def generate(
        self,
        *,
        messages: list[ModelMessage],
        output_schema: type[StructuredOutput],
        max_output_tokens: int = 2000,
        metadata: dict[str, Any] | None = None,
    ) -> ModelResult:
        payload = {
            "model": self._model,
            "messages": [
                {"role": message.role, "content": message.content} for message in messages
            ],
            "max_tokens": max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": output_schema.__name__,
                    "strict": True,
                    "schema": output_schema.model_json_schema(),
                },
            },
        }
        if metadata:
            payload["metadata"] = metadata
        response = await self._post_with_retry(payload)
        try:
            body = response.json()
            raw_content = body["choices"][0]["message"]["content"]
            data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
            output: BaseModel = output_schema.model_validate(data)
            usage_data = body.get("usage", {})
            return ModelResult(
                output=output,
                model=str(body.get("model", self._model)),
                request_id=response.headers.get("x-request-id"),
                usage=ModelUsage(
                    input_tokens=int(usage_data.get("prompt_tokens", 0)),
                    output_tokens=int(usage_data.get("completion_tokens", 0)),
                ),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError) as error:
            raise ExternalServiceFailure("Model returned an invalid structured response") from error

    async def _post_with_retry(self, payload: dict[str, Any]) -> httpx.Response:
        for attempt in range(self._max_retries + 1):
            try:
                response = await self._client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                    timeout=self._timeout_seconds,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self._max_retries:
                        await asyncio.sleep(min(0.1 * (2**attempt), 1.0))
                        continue
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as error:
                if attempt >= self._max_retries:
                    raise ExternalServiceFailure("Model request failed") from error
                await asyncio.sleep(min(0.1 * (2**attempt), 1.0))
        raise ExternalServiceFailure("Model request failed")
