from collections.abc import Hashable, Sequence


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[Hashable]], *, rank_constant: int = 60
) -> list[tuple[Hashable, float]]:
    if rank_constant <= 0:
        raise ValueError("rank_constant must be positive")
    scores: dict[Hashable, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (rank_constant + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))
