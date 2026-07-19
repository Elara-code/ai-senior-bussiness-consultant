import pytest
from pydantic import ValidationError

from consultant.adapters.llm.fake_model import FakeStructuredModel
from consultant.agents.schemas import RequirementAnalysisOutput
from consultant.ports.model import ModelMessage


@pytest.mark.asyncio
async def test_fake_model_validates_structured_output() -> None:
    model = FakeStructuredModel(
        [
            {
                "summary": "Manual reporting is slow.",
                "claims": [],
                "requirements": [],
                "information_gaps": ["Monthly report volume"],
                "interview_questions": ["How many reports are produced?"],
            }
        ]
    )

    result = await model.generate(
        messages=[ModelMessage(role="user", content="Analyze")],
        output_schema=RequirementAnalysisOutput,
    )

    assert isinstance(result.output, RequirementAnalysisOutput)
    assert result.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_fake_model_rejects_invalid_schema() -> None:
    model = FakeStructuredModel([{"summary": "Missing required fields"}])

    with pytest.raises(ValidationError):
        await model.generate(
            messages=[ModelMessage(role="user", content="Analyze")],
            output_schema=RequirementAnalysisOutput,
        )
