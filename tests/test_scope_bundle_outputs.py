"""Complete generated artifacts obey the same live session as query responses."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.adapters.generated_files import apply_generated
from mindgarden.application.federation import build_federation
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.application.site import build_site
from mindgarden.domain.contracts import canonical_json
from mindgarden.domain.validation import ContractError
from tests.federation_fixture import create_fixture
from tests.site_fixture import create_fixture as create_site_fixture
from tests.support_v1 import add_knowledge, write_json


class ScopeBundleOutputTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = create_fixture(self.root / "public")
        self.context = self.fixture["context"]

    def limit(self, maximum, fixture=None):
        fixture = fixture or self.fixture
        session = json.loads(fixture["session_path"].read_bytes())
        session["budgets"]["max_output_bytes"] = maximum
        write_json(fixture["session_path"], session)
        return QueryContext.load(fixture["configuration"], fixture["session_path"])

    def test_federation_limit_covers_sum_of_members_and_owned_metadata(self):
        files = self.fixture["bundle"].files
        limit = sum(map(len, files.values())) - 1
        self.assertGreater(limit, max(map(len, files.values())))
        with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
            build_federation(self.limit(limit), self.fixture["profile"])
        self.assertEqual(list(self.fixture["export"].iterdir()), [])

    def test_small_explicit_export_does_not_pay_for_the_entire_internal_index(self):
        profile = deepcopy(self.fixture["profile"])
        for number in range(12):
            record = add_knowledge(
                self.fixture["workspace"],
                f"unselected-{number}",
                visibility="public",
                body="Synthetic unselected corpus. " * 100,
                sources=self.fixture["evidence"],
            )
            record["publication"] = "eligible"
            write_json(
                self.fixture["workspace"]
                / ".garden/knowledge"
                / (record["id"] + ".json"),
                record,
            )
        session = json.loads(self.fixture["session_path"].read_bytes())
        write_json(
            self.fixture["session_path"],
            bind_session_revisions(self.fixture["configuration"], session),
        )
        context = QueryContext.load(
            self.fixture["configuration"], self.fixture["session_path"]
        )
        index = build_index(context)
        profile["source_revision"] = index["inputs"][0]["revision"]
        expected = build_federation(context, profile).files
        maximum = sum(map(len, expected.values()))
        self.assertGreater(len(canonical_json(index)), maximum)
        context = self.limit(maximum)
        self.assertEqual(build_federation(context, profile).files, expected)
        with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
            build_index(context)

    def test_site_content_and_manifest_share_the_whole_bundle_limit(self):
        fixture = create_site_fixture(self.root / "site")
        projection = build_site(fixture["context"], fixture["profile"])
        limit = sum(map(len, projection.files.values())) - 1
        with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
            build_site(self.limit(limit, fixture), fixture["profile"])
        self.assertEqual(list(fixture["export"].iterdir()), [])

    def rendered_fixture(self):
        fixture = create_site_fixture(self.root / "site")
        projection = build_site(fixture["context"], fixture["profile"])
        limit = sum(map(len, projection.files.values())) + 4096
        context = self.limit(limit, fixture)
        projection = build_site(context, fixture["profile"])
        engine = fixture["workspace"] / ".cache/mindgarden/renderer"
        engine.mkdir(parents=True)
        plan = projection.plan(
            context, fixture["export"], operation="build", engine_directory=engine
        )
        return fixture, projection, context, engine, plan, limit

    def test_oversized_rendered_output_denies_before_selecting_any_files(self):
        fixture, projection, context, engine, plan, limit = self.rendered_fixture()
        with (
            patch(
                "mindgarden.adapters.quartz.render_public_site",
                return_value={"index.html": b"x" * (limit + 1)},
            ),
            patch(
                "mindgarden.application.site.write_site",
                side_effect=AssertionError("Output selected"),
            ),
            self.assertRaisesRegex(ContractError, "QUERY_BUDGET"),
        ):
            projection.apply(
                context,
                fixture["export"],
                plan["plan_sha256"],
                operation="build",
                engine_directory=engine,
            )
        self.assertEqual(list(fixture["export"].iterdir()), [])

    def test_mid_render_revocation_stops_generation_before_output_selection(self):
        fixture, projection, context, engine, plan, _ = self.rendered_fixture()

        def revoke(*_):
            configuration = json.loads(fixture["configuration"].read_bytes())
            configuration["revoked_sessions"] = [context.session["id"]]
            write_json(fixture["configuration"], configuration)
            return {"index.html": b"Synthetic output"}

        with (
            patch("mindgarden.adapters.quartz.render_public_site", side_effect=revoke),
            self.assertRaisesRegex(ContractError, "SESSION_REVOKED"),
        ):
            projection.apply(
                context,
                fixture["export"],
                plan["plan_sha256"],
                operation="build",
                engine_directory=engine,
            )
        self.assertEqual(list(fixture["export"].iterdir()), [])

    def test_private_generated_marker_counts_before_directory_creation(self):
        context = self.limit(256)
        destination = self.root / "not-created/packet"
        with self.assertRaisesRegex(ContractError, "QUERY_BUDGET"):
            apply_generated(
                destination,
                {"packet.md": b"x" * 256},
                "0" * 64,
                "0" * 64,
                check_live=context.check_live,
                verify_inputs=lambda: None,
                validate_output=context.ensure_bundle,
            )
        self.assertFalse(destination.parent.exists())

    def test_live_authority_precedes_byte_limit_diagnostics(self):
        context = self.limit(256)
        configuration = json.loads(self.fixture["configuration"].read_bytes())
        configuration["revoked_sessions"] = [context.session["id"]]
        write_json(self.fixture["configuration"], configuration)
        for operation in (
            lambda: context.ensure_output(b"x" * 512),
            lambda: context.ensure_bundle({"private-name-canary": b"x" * 512}),
        ):
            with self.assertRaisesRegex(ContractError, "SESSION_REVOKED") as error:
                operation()
            self.assertNotIn("canary", str(error.exception))

    def test_invalid_generated_values_have_constant_diagnostics(self):
        for value in ([], {"private-name-canary": "private-content-canary"}):
            with self.assertRaisesRegex(ContractError, "QUERY_OUTPUT") as error:
                self.context.ensure_bundle(value)
            self.assertNotIn("canary", str(error.exception))


if __name__ == "__main__":
    unittest.main()
