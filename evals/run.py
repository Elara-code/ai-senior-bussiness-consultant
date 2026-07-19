import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evals.metrics import (
    citation_coverage,
    citation_precision,
    mean,
    recall_at_k,
    reciprocal_rank,
)


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    cases: int
    recall_at_8: float
    mrr: float
    citation_precision: float
    citation_coverage: float
    schema_success_rate: float
    forbidden_conclusion_rate: float
    unauthorized_disclosure_rate: float
    passed: bool


def evaluate(cases: list[dict[str, Any]]) -> EvaluationReport:
    recalls: list[float] = []
    ranks: list[float] = []
    precisions: list[float] = []
    coverages: list[float] = []
    schema_successes = 0
    forbidden = 0
    disclosures = 0
    for case in cases:
        expected = set(case["expected_evidence_ids"])
        retrieved = list(case["fake_prediction"]["retrieved_ids"])
        predicted = set(case["fake_prediction"]["citation_ids"])
        recalls.append(recall_at_k(expected, retrieved, 8))
        ranks.append(reciprocal_rank(expected, retrieved))
        precisions.append(citation_precision(expected, predicted))
        coverages.append(citation_coverage(expected, predicted))
        schema_successes += bool(case["fake_prediction"]["schema_valid"])
        forbidden += bool(case["fake_prediction"]["contains_forbidden_conclusion"])
        disclosures += bool(case["fake_prediction"]["unauthorized_disclosure"])
    count = len(cases)
    report = EvaluationReport(
        cases=count,
        recall_at_8=mean(recalls),
        mrr=mean(ranks),
        citation_precision=mean(precisions),
        citation_coverage=mean(coverages),
        schema_success_rate=schema_successes / count if count else 0.0,
        forbidden_conclusion_rate=forbidden / count if count else 0.0,
        unauthorized_disclosure_rate=disclosures / count if count else 0.0,
        passed=False,
    )
    passed = (
        report.citation_precision >= 0.95
        and report.citation_coverage >= 0.90
        and report.schema_success_rate >= 0.98
        and report.forbidden_conclusion_rate == 0
        and report.unauthorized_disclosure_rate == 0
    )
    return EvaluationReport(**{**asdict(report), "passed": passed})


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def markdown_report(report: EvaluationReport) -> str:
    return "\n".join(
        [
            "# Phase One Evaluation Report",
            "",
            f"- Cases: {report.cases}",
            f"- Recall@8: {report.recall_at_8:.3f}",
            f"- MRR: {report.mrr:.3f}",
            f"- Citation precision: {report.citation_precision:.3f}",
            f"- Citation coverage: {report.citation_coverage:.3f}",
            f"- Schema success: {report.schema_success_rate:.3f}",
            f"- Forbidden conclusion rate: {report.forbidden_conclusion_rate:.3f}",
            f"- Unauthorized disclosure rate: {report.unauthorized_disclosure_rate:.3f}",
            f"- Quality gate: {'PASS' if report.passed else 'FAIL'}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["fake"], default="fake")
    parser.add_argument(
        "--dataset", type=Path, default=Path("evals/datasets/phase1.jsonl")
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    report = evaluate(load_cases(args.dataset))
    print(markdown_report(report))
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "report.json").write_text(
            json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n"
        )
        (args.output_dir / "report.md").write_text(markdown_report(report) + "\n")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
