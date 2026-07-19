from pathlib import Path

from evals.metrics import citation_coverage, citation_precision, recall_at_k, reciprocal_rank
from evals.run import evaluate, load_cases


def test_retrieval_and_citation_metrics() -> None:
    assert recall_at_k({"a", "b"}, ["a", "c", "b"], 2) == 0.5
    assert reciprocal_rank({"b"}, ["a", "b"]) == 0.5
    assert citation_precision({"a"}, {"a", "x"}) == 0.5
    assert citation_coverage({"a", "b"}, {"a"}) == 0.5


def test_phase_one_fake_dataset_passes_quality_gate() -> None:
    cases = load_cases(Path("evals/datasets/phase1.jsonl"))
    report = evaluate(cases)

    assert len(cases) == 20
    assert report.passed is True
    assert report.citation_precision >= 0.95
    assert report.unauthorized_disclosure_rate == 0
