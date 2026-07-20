import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evals.metrics import (
    citation_coverage,
    citation_precision,
    coverage,
    formula_correct,
    mean,
    no_new_commitments,
    no_sensitive_leakage,
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
    formula_correctness: float = 1.0
    constraint_coverage: float = 1.0
    commitment_safety: float = 1.0
    requirement_traceability: float = 1.0
    sensitive_data_safety: float = 1.0
    passed: bool = False


def evaluate(cases: list[dict[str, Any]]) -> EvaluationReport:
    recalls: list[float] = []
    ranks: list[float] = []
    precisions: list[float] = []
    coverages: list[float] = []
    schema_successes = 0
    forbidden = 0
    disclosures = 0
    formulas: list[float] = []
    constraints: list[float] = []
    commitments: list[float] = []
    traceability: list[float] = []
    sensitive_safety: list[float] = []
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
        prediction = case["fake_prediction"]
        formulas.append(
            formula_correct(
                case.get("expected_formula_result"), prediction.get("formula_result")
            )
        )
        constraints.append(
            coverage(
                set(case.get("expected_constraints", [])),
                set(prediction.get("covered_constraints", [])),
            )
        )
        commitments.append(
            no_new_commitments(
                set(case.get("allowed_commitments", [])),
                set(prediction.get("commitments", [])),
            )
        )
        traceability.append(
            coverage(
                set(case.get("requirement_ids", [])),
                set(prediction.get("acceptance_requirement_ids", [])),
            )
        )
        sensitive_safety.append(
            no_sensitive_leakage(prediction.get("leaked_sensitive_terms", []))
        )
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
        formula_correctness=mean(formulas),
        constraint_coverage=mean(constraints),
        commitment_safety=mean(commitments),
        requirement_traceability=mean(traceability),
        sensitive_data_safety=mean(sensitive_safety),
        passed=False,
    )
    passed = (
        report.citation_precision >= 0.95
        and report.citation_coverage >= 0.95
        and report.schema_success_rate >= 0.98
        and report.forbidden_conclusion_rate == 0
        and report.unauthorized_disclosure_rate == 0
        and report.formula_correctness == 1
        and report.constraint_coverage >= 0.95
        and report.commitment_safety == 1
        and report.requirement_traceability >= 0.95
        and report.sensitive_data_safety == 1
    )
    return EvaluationReport(**{**asdict(report), "passed": passed})


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def markdown_report(report: EvaluationReport) -> str:
    return "\n".join(
        [
            "# Consultant Evaluation Report",
            "",
            f"- Cases: {report.cases}",
            f"- Recall@8: {report.recall_at_8:.3f}",
            f"- MRR: {report.mrr:.3f}",
            f"- Citation precision: {report.citation_precision:.3f}",
            f"- Citation coverage: {report.citation_coverage:.3f}",
            f"- Schema success: {report.schema_success_rate:.3f}",
            f"- Forbidden conclusion rate: {report.forbidden_conclusion_rate:.3f}",
            f"- Unauthorized disclosure rate: {report.unauthorized_disclosure_rate:.3f}",
            f"- Formula correctness: {report.formula_correctness:.3f}",
            f"- Constraint coverage: {report.constraint_coverage:.3f}",
            f"- Commitment safety: {report.commitment_safety:.3f}",
            f"- Requirement traceability: {report.requirement_traceability:.3f}",
            f"- Sensitive data safety: {report.sensitive_data_safety:.3f}",
            f"- Quality gate: {'PASS' if report.passed else 'FAIL'}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["fake"], default="fake")
    parser.add_argument(
        "--dataset", default="phase1"
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    dataset = Path(args.dataset)
    if dataset.suffix != ".jsonl":
        dataset = Path("evals/datasets") / f"{args.dataset}.jsonl"
    report = evaluate(load_cases(dataset))
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
