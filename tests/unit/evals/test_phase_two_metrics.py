from pathlib import Path

from evals.metrics import coverage, formula_correct, no_new_commitments, no_sensitive_leakage
from evals.run import evaluate, load_cases


def test_phase_two_metric_primitives_reject_quality_regressions() -> None:
    assert coverage({"a", "b"}, {"a"}) == 0.5
    assert formula_correct(0.5, 0.5) == 1
    assert formula_correct(0.5, 0.6) == 0
    assert no_new_commitments({"pilot"}, {"pilot", "production"}) == 0
    assert no_sensitive_leakage(["customer@example.jp"]) == 0


def test_phase_two_dataset_meets_quality_gate() -> None:
    report = evaluate(load_cases(Path("evals/datasets/phase2.jsonl")))
    assert report.passed
    assert report.citation_coverage >= 0.95
    assert report.sensitive_data_safety == 1
