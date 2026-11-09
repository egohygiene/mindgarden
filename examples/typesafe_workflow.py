#!/usr/bin/env python3
"""Optional synthetic Jev intent -> ordinary authorized Garden read handler.

No arbitrary source/archive inputs. Hosted request text is a fixed public fixture.
"""

from argparse import ArgumentParser
import json
import importlib.util
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if importlib.util.find_spec("mindgarden") is None:
    sys.path.insert(0, str(ROOT / "src"))
from mindgarden.application.semantic_workflow import (
    suggest_read_workflow,
    dispatch_read_workflow,
)
from mindgarden.domain.contracts import canonical_json


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-hosted",
        action="store_true",
        help="Permit sending only the fixed synthetic request to the configured TypeSafe service",
    )
    args = parser.parse_args()
    decision = suggest_read_workflow(
        "Find reviewed knowledge about prompt templates.",
        allow_hosted=args.allow_hosted,
    )
    report = {
        "schema": "mindgarden.synthetic-semantic-workflow/v1",
        "decision": decision.as_dict(),
        "model_accuracy": "not-measured",
        "input": "fixed-public-synthetic-request",
    }
    if decision.outcome == "selected":
        sys.path.insert(0, str(ROOT))
        from tests.insight_fixture import setup

        with tempfile.TemporaryDirectory() as tmp:
            fixture, _ = setup(Path(tmp))
            report["read_result"] = dispatch_read_workflow(
                fixture["context"],
                decision,
                query="prompt",
                target="repository-garden/reviewed-reference",
            )
            fixture["context"].ensure_output(canonical_json(report))
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
