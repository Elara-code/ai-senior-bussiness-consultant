from dataclasses import dataclass
from typing import Literal

from consultant.agents.schemas import (
    FinancialScenarioOutput,
    RiskOutput,
    ValueRiskOutput,
)
from consultant.domain.business_loop import BusinessParameter


@dataclass(frozen=True, slots=True)
class ValueRiskInputs:
    annual_hours_saved: BusinessParameter
    hourly_cost: BusinessParameter
    annual_platform_cost: BusinessParameter


def calculate_value_risk(inputs: ValueRiskInputs) -> ValueRiskOutput:
    issues = [
        f"{parameter.name} must be positive"
        for parameter in (
            inputs.annual_hours_saved,
            inputs.hourly_cost,
            inputs.annual_platform_cost,
        )
        if parameter.value < 0
    ]
    scenarios = [
        _scenario("conservative", inputs, benefit_factor=0.7, cost_factor=1.15),
        _scenario("base", inputs, benefit_factor=1.0, cost_factor=1.0),
        _scenario("optimistic", inputs, benefit_factor=1.2, cost_factor=0.95),
    ]
    return ValueRiskOutput(
        scenarios=scenarios,
        risks=[
            RiskOutput(
                name="业务采纳不足",
                likelihood="medium",
                impact="high",
                mitigation="先灰度试点并按真实采纳率校准收益",
            )
        ],
        assumptions=["收益按节省工时乘以综合小时成本计算"],
        quality_issues=issues,
    )


def _scenario(
    name: Literal["conservative", "base", "optimistic"],
    inputs: ValueRiskInputs,
    *,
    benefit_factor: float,
    cost_factor: float,
) -> FinancialScenarioOutput:
    benefit = inputs.annual_hours_saved.value * inputs.hourly_cost.value * benefit_factor
    cost = inputs.annual_platform_cost.value * cost_factor
    net = benefit - cost
    roi = net / cost if cost else None
    return FinancialScenarioOutput(
        name=name, annual_benefit=benefit, annual_cost=cost, net_value=net, roi=roi
    )
