#!/usr/bin/env python3
"""Run the synthetic offline publication conformance pack against a source or installed engine."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.domain.contracts import canonical_json

SUITES = ("tests.test_publication_conformance", "tests.test_publish_garden", "tests.test_v1_validation",
          "tests.test_exact_evidence", "tests.test_scoped_retrieval", "tests.test_federation", "tests.test_site")


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Create a fresh shareable JSON report")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("This pack requires the source engine from this checkout")
    if arguments.require_installed and (engine.is_relative_to(ROOT / "src") or not engine.is_relative_to(Path(sys.prefix).resolve())):
        parser.error("This pack requires the installed engine in this interpreter prefix")
    sys.path.insert(0, str(ROOT))
    private_log = io.StringIO()
    with redirect_stdout(private_log), redirect_stderr(private_log):
        suite = unittest.defaultTestLoader.loadTestsFromNames(SUITES)
        result = unittest.TextTestRunner(stream=private_log, verbosity=1).run(suite)
    report = {"schema": "mindgarden.publication-conformance/v1", "status": "passed" if result.wasSuccessful() and not result.skipped else "incomplete",
              "engine_version": mindgarden.__version__, "tests_run": result.testsRun, "skipped": len(result.skipped),
              "failed_tests": sorted(test.id() for test, _traceback in result.failures + result.errors),
              "surfaces": ["frontmatter", "markdown-body", "attachments", "links", "indexes", "errors", "build-logs", "metadata"],
              "coverage": "bounded-synthetic-publication-and-preview", "retained_gates": ["consumer-acceptance", "restricted-runtime-assurance", "full-media-coverage"]}
    if arguments.report:
        with arguments.report.open("xb") as stream: stream.write(canonical_json(report))
    print(canonical_json(report).decode(), end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
