"""Optional real Mindcap producer → dependency-free Mindgarden adapter proof."""

from argparse import ArgumentParser
from pathlib import Path
import sys
import json
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.adapters.captured_source import CapturedSourceAdapter
from mindgarden.application.bookmarks import read_metadata
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.sources import check_adapter_conformance, normalize_source


def check(fixture_directory):
    # Optional verification environment only; never imported by the engine.
    from mindcap.contracts.source_bundle import handoff_schema
    from mindcap.core.models import CaptureRequest
    from mindcap.plugins.chrome_bookmarks.handoff import bookmark_source_bundle
    from mindcap.plugins.chrome_bookmarks.plugin import ChromeBookmarksPlugin

    assert handoff_schema() == json.loads(
        (ROOT / "contracts/v1/captured-source-bundle.schema.json").read_text()
    )
    source_sets, packages, cleanup_sets = [], [], []
    with (
        tempfile.TemporaryDirectory() as temporary,
        patch("socket.socket", side_effect=AssertionError("Network attempted")),
    ):
        for observation in ("first", "second"):
            plugin = ChromeBookmarksPlugin()
            request = CaptureRequest(
                source_type="chrome-bookmarks",
                source="",
                provider="chrome-bookmarks",
                canonical_identifier="local",
                strategy="filesystem",
                artifact_root=Path(temporary) / observation,
                options={
                    "user_data_dirs": [str(fixture_directory)],
                    "channel": "stable",
                },
            )
            envelope = plugin.strategy("filesystem").capture(request)
            normalized = plugin.normalize(envelope, "local")
            captured = plugin.storage().persist(
                request, envelope, normalized, plugin.render(normalized)
            )
            identities = {
                item["profile_id"]: "synthetic-"
                + item["profile_directory_name"].lower().replace(" ", "-")
                for item in normalized["profiles"]
            }
            packaged = bookmark_source_bundle(
                captured.path,
                source_id="synthetic-browser",
                producer_revision="7ee766c1c34adad239fc602499f624979a2d9cac",
                profile_identities=identities,
            )
            packages.append(packaged)
            check_adapter_conformance(CapturedSourceAdapter(), packaged, {})
            bundle = normalize_source(CapturedSourceAdapter(), packaged, {})
            private_input = Path(temporary) / (observation + ".zip")
            private_input.write_bytes(packaged)
            _source, bookmarks = read_metadata(
                private_input, "personal", input_format="captured-source-bundle"
            )
            assert len(bookmarks) == len(bundle.units)
            assert all(item["page_content"] == "not-captured" for item in bookmarks)
            cleanup_sets.append(
                {
                    item["id"]: {
                        key: item["evidence"][key]
                        for key in (
                            "source_identity",
                            "sha256",
                            "locators",
                            "original_selector",
                        )
                    }
                    for item in bookmarks
                }
            )
            for unit in bundle.units:
                assert str(fixture_directory).encode() not in unit.content
                assert str(temporary).encode() not in canonical_json(unit.metadata)
            source_sets.append({unit.identity: unit.content for unit in bundle.units})
    assert packages[0] != packages[1]
    assert source_sets[0] == source_sets[1]
    assert cleanup_sets[0] == cleanup_sets[1]
    return {
        "schema": "mindgarden.capture-handoff-proof/v1",
        "status": "passed",
        "producer_commit": "7ee766c1c34adad239fc602499f624979a2d9cac",
        "source_contract": "mindcap.captured-source-bundle/v1",
        "observations": 2,
        "units_per_observation": len(source_sets[0]),
        "stable_unit_content": "equal",
        "private_cleanup_evidence": "stable-normalized-metadata-exact-observation-lineage",
        "raw_capture_packages": "distinct-and-preserved",
        "network": "blocked-in-process",
        "model": "unused",
        "google": "unused",
        "scope": "synthetic-private-only",
    }


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    arguments = parser.parse_args()
    content = canonical_json(check(arguments.fixture_directory.absolute()))
    if arguments.report:
        with arguments.report.open("xb") as output:
            output.write(content)
    print(content.decode(), end="")
