"""Audit labeled examples or explicitly evaluate a bounded synthetic live subset."""

from argparse import ArgumentParser
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.application.semantic_workflow import suggest_read_workflow
from mindgarden.domain.contracts import canonical_json


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    dataset = json.loads(
        (ROOT / "tests/fixtures/semantic-workflow/evaluation.json").read_text()
    )
    cases = dataset["cases"]
    if not 1 <= args.limit <= len(cases):
        parser.error("limit must select a bounded subset of the synthetic fixture")
    results = []
    if args.live:
        for case in cases[: args.limit]:
            decision = suggest_read_workflow(case["text"], allow_hosted=True)
            evaluated = decision.resolved_model is not None
            results.append(
                {
                    "id": case["id"],
                    "expected_route": case["expected_route"],
                    "decision": decision.as_dict(),
                    "model_evaluated": evaluated,
                    "matches_label": (
                        decision.route == case["expected_route"]
                        and (
                            decision.outcome == "selected"
                            if case["category"] == "clear"
                            else decision.outcome in {"clarify", "unsupported"}
                        )
                    )
                    if evaluated
                    else None,
                }
            )
    evaluated = [r for r in results if r["model_evaluated"]]
    report = {
        "schema": "mindgarden.semantic-evaluation-report/v1",
        "mode": "live-synthetic" if args.live else "dataset-audit",
        "labeled_cases": len(cases),
        "categories": sorted({c["category"] for c in cases}),
        "predictions": results,
        "evaluated_by_model": len(evaluated),
        "accuracy": sum(r["matches_label"] for r in evaluated) / len(evaluated)
        if evaluated
        else None,
        "resolved_models": sorted({r["decision"]["resolved_model"] for r in evaluated}),
        "thresholds": "provisional; fixture labels and software mocks do not establish model accuracy",
        "live_required_setup": "TYPESAFE_ENABLED=true and server-side TYPESAFE_API_KEY; no secret values in reports",
    }
    content = canonical_json(report)
    if args.report:
        args.report.write_bytes(content)
    print(content.decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
