from consultant.adapters.retrieval.rrf import reciprocal_rank_fusion


def test_rrf_rewards_items_present_in_multiple_rankings() -> None:
    fused = reciprocal_rank_fusion([["a", "b"], ["b", "c"]], rank_constant=10)

    assert fused[0][0] == "b"
    assert {item for item, _ in fused} == {"a", "b", "c"}
