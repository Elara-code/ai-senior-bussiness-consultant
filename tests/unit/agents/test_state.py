from consultant.agents.nodes import plan_node
from consultant.agents.state import ConsultantAgentState


def test_plan_rejects_unbounded_agent_steps() -> None:
    state: ConsultantAgentState = {"max_steps": 21}

    try:
        plan_node(state)
    except ValueError as error:
        assert "between 1 and 20" in str(error)
    else:
        raise AssertionError("Expected max_steps validation")
