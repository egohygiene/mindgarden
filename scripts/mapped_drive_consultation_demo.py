#!/usr/bin/env python3
"""Offline mapped Drive capture to reviewed knowledge, context and vault recovery."""

from argparse import ArgumentParser
from functools import partial
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.domain.contracts import canonical_json, digest_bytes

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from consultation_demo import run_demo as run_packet_demo
from drive_consultation_demo import captured_fixture
from tests.mapped_drive_fixture import MappedFixtureDrive, normalization


def run_demo(workspace):
    configuration = normalization()
    factory = partial(
        captured_fixture, provider=MappedFixtureDrive(), normalization=configuration
    )
    report = run_packet_demo(workspace, fixture_factory=factory)
    report.update(
        schema="mindgarden.synthetic-mapped-drive-proof/v1",
        google="synthetic-provider-only; no account or OAuth",
        normalization={
            "configuration_revision": "sha256:"
            + digest_bytes(canonical_json(configuration)),
            "mapped_provider_files": 3,
            "layouts": ["signed-iso-date", "debit-credit-us-date"],
            "snapshots": 2,
            "reused_unchanged_rows": 8,
            "original_occurrences": 9,
            "instruction_authority": "none; captured bytes and mappings are source data",
        },
    )
    return report


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check-golden", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--require-source", action="store_true")
    mode.add_argument("--require-installed", action="store_true")
    arguments = parser.parse_args()
    engine = Path(mindgarden.__file__).resolve()
    if arguments.require_source and not engine.is_relative_to(ROOT / "src"):
        parser.error("Exact source engine required")
    if arguments.require_installed and (
        engine.is_relative_to(ROOT / "src")
        or not engine.is_relative_to(Path(sys.prefix).resolve())
    ):
        parser.error("Installed engine required")
    encoded = canonical_json(run_demo(arguments.workspace))
    golden = ROOT / "tests/fixtures/consultation/expected-mapped-drive-proof.json"
    if arguments.check_golden and encoded != golden.read_bytes():
        raise AssertionError(
            "Complete mapped Drive proof differs from its committed golden"
        )
    if arguments.report:
        with arguments.report.open("xb") as output:
            output.write(encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
