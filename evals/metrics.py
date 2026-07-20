from collections.abc import Sequence


def recall_at_k(expected: set[str], retrieved: Sequence[str], k: int) -> float:
    if not expected:
        return 1.0
    if k <= 0:
        raise ValueError("k must be positive")
    return len(expected & set(retrieved[:k])) / len(expected)


def reciprocal_rank(expected: set[str], retrieved: Sequence[str]) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if item in expected:
            return 1.0 / rank
    return 0.0 if expected else 1.0


def citation_precision(expected: set[str], predicted: set[str]) -> float:
    if not predicted:
        return 1.0 if not expected else 0.0
    return len(expected & predicted) / len(predicted)


def citation_coverage(expected: set[str], predicted: set[str]) -> float:
    if not expected:
        return 1.0
    return len(expected & predicted) / len(expected)


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def coverage(expected: set[str], observed: set[str]) -> float:
    """Return deterministic coverage for constraints and traceability identifiers."""
    return 1.0 if not expected else len(expected & observed) / len(expected)


def formula_correct(
    expected: float | int | None,
    observed: float | int | None,
    tolerance: float = 1e-6,
) -> float:
    if expected is None:
        return 1.0
    if observed is None:
        return 0.0
    return float(abs(float(expected) - float(observed)) <= tolerance)


def no_new_commitments(allowed: set[str], proposed: set[str]) -> float:
    return float(proposed <= allowed)


def no_sensitive_leakage(leaked_terms: Sequence[str]) -> float:
    return float(not leaked_terms)
