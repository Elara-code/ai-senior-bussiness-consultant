from uuid import uuid4

from consultant.agents.value_risk_agent import ValueRiskInputs, calculate_value_risk
from consultant.domain.business_loop import BusinessParameter


def parameter(name: str, value: float) -> BusinessParameter:
    return BusinessParameter(name=name, value=value, confirmed_by=uuid4())


def test_value_agent_calculates_three_deterministic_scenarios() -> None:
    result = calculate_value_risk(
        ValueRiskInputs(
            annual_hours_saved=parameter("hours", 1000),
            hourly_cost=parameter("cost", 100),
            annual_platform_cost=parameter("platform", 40000),
        )
    )
    assert [item.name for item in result.scenarios] == [
        "conservative", "base", "optimistic"
    ]
    assert result.scenarios[1].annual_benefit == 100000
    assert result.scenarios[1].roi == 1.5
    assert result.quality_issues == []
