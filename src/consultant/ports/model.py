from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True, slots=True)
class ModelResult:
    output: BaseModel
    model: str
    request_id: str | None = None
    usage: ModelUsage = field(default_factory=ModelUsage)


class StructuredModel(Protocol):
    async def generate(
        self,
        *,
        messages: list[ModelMessage],
        output_schema: type[StructuredOutput],
        max_output_tokens: int = 2000,
        metadata: dict[str, Any] | None = None,
    ) -> ModelResult: ...
