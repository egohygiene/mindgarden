"""Optional real Mindcap producer → dependency-free Mindgarden adapter proof."""

from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.adapters.captured_source import CapturedSourceAdapter
from mindgarden.application.bookmarks import read_metadata
from mindgarden.domain.contracts import canonical_json, digest_bytes
from mindgarden.domain.scope import POLICY_REFERENCE
from mindgarden.domain.sources import check_adapter_conformance, normalize_source
from mindgarden.interfaces.cli import main


def write_control(path, content):
    with path.open("xb") as stream:
        path.chmod(0o600)
        stream.write(canonical_json(content))


def rehearse_cleanup(source, later_source, workspace):
    """Exercise the normal CLI at the actual producer boundary with two fixture rows."""
    workspace.mkdir(mode=0o700)
    catalog = workspace / "catalog.json"
    write_control(
        catalog, {"schema": "mindgarden.local-bookmark-catalog/v1", "urls": []}
    )
    command = [
        "bookmarks",
        "--classification",
        "personal",
        "--input-format",
        "captured-source-bundle",
        "--input",
        str(source),
        "--catalog",
        str(catalog),
    ]

    summaries = []

    def run(arguments, expected_code=0):
        with (
            redirect_stdout(StringIO()) as stdout,
            redirect_stderr(StringIO()) as stderr,
        ):
            assert main(arguments) == expected_code, "Synthetic bookmark CLI failed"
        summaries.extend([stdout.getvalue(), stderr.getvalue()])
        return (
            json.loads(stdout.getvalue()) if expected_code == 0 else stderr.getvalue()
        )

    inventory_path = workspace / "inventory.json"
    inventory = run(command + ["--inspect", "--plan-file", str(inventory_path)])
    assert inventory["status"] == "private-inventory-written"
    inspection = json.loads(inventory_path.read_bytes())
    records = inspection["records"]
    assert len(records) == 2
    assert inspection["capture"]["status"] == "complete"
    assert inventory["sha256"] == digest_bytes(inventory_path.read_bytes())
    retained = next(
        record for record in records if record["url"].startswith("https://")
    )
    excluded = next(
        record for record in records if record["url"].startswith("obsidian://")
    )

    decisions = []
    for record in records:
        action = "rename" if record == retained else "quarantine"
        decisions.append(
            {
                "id": record["id"],
                "action": action,
                "rationale": "Authored decision for the synthetic rehearsal.",
                "new_title": "Reviewed synthetic bookmark"
                if action == "rename"
                else None,
                "new_folders": None,
                "merge_into": None,
                "public_approval": False,
            }
        )
    base_request = {
        "schema": "mindgarden.bookmark-review-request/v1",
        "source_sha256": inspection["source_sha256"],
        "catalog_sha256": inspection["catalog_sha256"],
        "policy": POLICY_REFERENCE,
        "review": {
            "state": "approved",
            "reviewers": ["synthetic-reviewer"],
            "reviewed_at": "2026-11-20T00:00:00Z",
            "rationale": "Synthetic private cleanup rehearsal only.",
        },
        "review_authority": {"kind": "human", "id": "synthetic-reviewer"},
    }

    def batch(name, offset, selected, prior=None):
        request_path = workspace / f"{name}-request.json"
        plan_path = workspace / f"{name}-plan.json"
        output = workspace / f"{name}-output"
        write_control(
            request_path,
            {
                **base_request,
                "offset": offset,
                "limit": len(selected),
                "decisions": selected,
                "prior_receipt_sha256": digest_bytes(prior.read_bytes())
                if prior
                else None,
            },
        )
        arguments = command + [
            "--request",
            str(request_path),
            "--plan-file",
            str(plan_path),
        ]
        if prior:
            arguments += ["--previous-receipt", str(prior)]
        result = run(arguments)
        assert result["status"] == "private-plan-written"
        plan = json.loads(plan_path.read_bytes())
        assert result["plan_sha256"] == plan["plan_sha256"]
        apply = arguments + [
            "--apply",
            "--plan-digest",
            plan["plan_sha256"],
            "--output-directory",
            str(output),
        ]
        assert run(apply)["status"] == "created"
        assert run(apply)["status"] == "verified-no-op"
        assert (output / "captured-source.zip").read_bytes() == source.read_bytes()
        assert plan_path.stat().st_mode & 0o777 == 0o600
        return output, plan, apply

    first_output, first_plan, _ = batch("first", 0, decisions[:1])
    assert first_plan["next_offset"] == 1
    assert not json.loads((first_output / "cleaned-bookmarks.json").read_bytes())[
        "complete_review"
    ]
    resumed, final_plan, apply = batch(
        "resumed", 1, decisions[1:], first_output / "review-receipt.json"
    )
    one_pass, _, _ = batch("one-pass", 0, decisions)
    assert final_plan["next_offset"] is None
    for name in ("cleaned-bookmarks.html", "cleaned-bookmarks.json", "quarantine.json"):
        assert (resumed / name).read_bytes() == (one_pass / name).read_bytes()
    cleaned = json.loads((resumed / "cleaned-bookmarks.json").read_bytes())
    assert cleaned["complete_review"]
    assert [record["url"] for record in cleaned["records"]] == [retained["url"]]
    html = (resumed / "cleaned-bookmarks.html").read_bytes()
    assert b"Reviewed synthetic bookmark" in html
    assert excluded["url"].encode() not in html
    quarantine = json.loads((resumed / "quarantine.json").read_bytes())["items"]
    assert [(item["record"]["id"], item["reason"]) for item in quarantine] == [
        (excluded["id"], "unsupported-url")
    ]
    stale = workspace / "stale-output"
    apply[apply.index("--input") + 1] = str(later_source)
    apply[apply.index("--output-directory") + 1] = str(stale)
    assert "BOOKMARK_STALE" in run(apply, expected_code=3)
    assert not stale.exists()
    assert digest_bytes(source.read_bytes()) == inspection["source_sha256"]
    handoff = json.loads((resumed / "akashic-handoff-status.json").read_bytes())
    assert handoff["state"] == "unavailable" and handoff["publication"] == "denied"
    assert set(handoff) == {
        "state",
        "publication",
        "schema",
        "owner_contract",
        "reason",
    }
    console = "".join(summaries)
    assert str(workspace.parent) not in console
    for record in records:
        assert record["url"] not in console and record["title"] not in console
    return {
        "batch_sizes": [1, 1],
        "replay": "verified-no-op",
        "resumed_exports": "byte-identical-to-single-batch",
        "changed_capture": "prior-approval-rejected-before-write",
        "original_zip": "byte-identical",
        "console": "summary-only",
        "reviewed_export": "renamed-https-retained-application-url-quarantined",
        "akashic_handoff": "explicitly-unavailable",
    }


def check(fixture_directory, *, rehearse_private_cleanup=False):
    # Optional verification environment only; never imported by the engine.
    from mindcap.contracts.source_bundle import handoff_schema
    from mindcap.core.models import CaptureRequest
    from mindcap.plugins.chrome_bookmarks.handoff import bookmark_source_bundle
    from mindcap.plugins.chrome_bookmarks.plugin import ChromeBookmarksPlugin

    assert handoff_schema() == json.loads(
        (ROOT / "contracts/v1/captured-source-bundle.schema.json").read_text()
    )
    source_sets, packages, cleanup_sets = [], [], []
    rehearsal = None
    with (
        tempfile.TemporaryDirectory(
            dir=Path(tempfile.gettempdir()).resolve()
        ) as temporary,
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
            private_input.chmod(0o600)
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
        if rehearse_private_cleanup:
            workspace = Path(temporary)
            rehearsal = rehearse_cleanup(
                workspace / "first.zip", workspace / "second.zip", workspace / "review"
            )
    assert packages[0] != packages[1]
    assert source_sets[0] == source_sets[1]
    assert cleanup_sets[0] == cleanup_sets[1]
    result = {
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
    if rehearsal is not None:
        result["private_cli_cleanup_rehearsal"] = rehearsal
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-directory", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--rehearse-private-cleanup", action="store_true")
    arguments = parser.parse_args()
    content = canonical_json(
        check(
            arguments.fixture_directory.absolute(),
            rehearse_private_cleanup=arguments.rehearse_private_cleanup,
        )
    )
    if arguments.report:
        with arguments.report.open("xb") as output:
            output.write(content)
    print(content.decode(), end="")
