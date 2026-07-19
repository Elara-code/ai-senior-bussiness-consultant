from collections import deque
from typing import Any

from pydantic import BaseModel

from consultant.ports.model import ModelMessage, ModelResult, ModelUsage, StructuredOutput


class FakeStructuredModel:
    def __init__(self, responses: list[dict[str, Any]], *, model: str = "fake-model") -> None:
        self._responses = deque(responses)
        self.model = model
        self.calls: list[list[ModelMessage]] = []

    async def generate(
        self,
        *,
        messages: list[ModelMessage],
        output_schema: type[StructuredOutput],
        max_output_tokens: int = 2000,
        metadata: dict[str, Any] | None = None,
    ) -> ModelResult:
        del metadata
        if max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")
        if not self._responses:
            raise RuntimeError("Fake model has no configured response")
        self.calls.append(messages)
        output: BaseModel = output_schema.model_validate(self._responses.popleft())
        return ModelResult(
            output=output,
            model=self.model,
            request_id=f"fake-{len(self.calls)}",
            usage=ModelUsage(
                input_tokens=sum(len(item.content) // 4 for item in messages),
                output_tokens=1,
            ),
        )
