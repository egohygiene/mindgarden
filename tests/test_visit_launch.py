"""The fixture assistant is an explicit option for the fictional Studio visit."""

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mindgarden.interfaces.cli import ExitCode, main
from mindgarden.domain.contracts import canonical_json, read_object
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.visit_demo import prepare_demo


class VisitLaunchTests(unittest.TestCase):
    def test_fixture_is_refused_before_preflight_or_startup(self):
        for arguments in (
            ["--demo", "--workspace", "fictional-workspace"],
            ["--local-config", "local-bindings.json", "--scope", "local-session.json", "--interface", "studio"],
        ):
            with (
                self.subTest(arguments=arguments),
                patch("mindgarden.interfaces.local_web.browser_assets") as assets,
                patch("mindgarden.interfaces.visit_demo.prepare_demo") as prepare,
                patch("mindgarden.interfaces.local_web.serve_garden") as serve,
                redirect_stderr(StringIO()) as diagnostics,
            ):
                result = main(["visit", *arguments, "--assistant", "fixture"])
                self.assertEqual(result, ExitCode.CONTRACT)
                self.assertIn("use --assistant fixture with --demo --interface studio", diagnostics.getvalue())
                assets.assert_not_called()
                prepare.assert_not_called()
                serve.assert_not_called()

    def test_fixture_starts_only_with_explicit_demo_studio(self):
        config, scope = Path("fictional-bindings.json"), Path("fictional-session.json")
        with (
            patch("mindgarden.interfaces.local_web.browser_assets") as assets,
            patch("mindgarden.interfaces.visit_demo.prepare_demo", return_value=(config, scope)) as prepare,
            patch("mindgarden.interfaces.local_web.serve_garden", return_value=0) as serve,
        ):
            result = main(["visit", "--demo", "--workspace", "fictional-workspace", "--interface", "studio",
                           "--assistant", "fixture", "--port", "1234"])
            self.assertEqual(result, ExitCode.SUCCESS)
            assets.assert_called_once_with("studio")
            prepare.assert_called_once_with(Path("fictional-workspace"), assistant=True)
            serve.assert_called_once_with(config, scope, port=1234, demo=True, interface="studio", assistant="fixture")

    def test_private_visits_default_to_assistant_off(self):
        config, scope = Path("local-bindings.json"), Path("local-session.json")
        for flags, interface in (([], "classic"), (["--interface", "studio"], "studio")):
            with (
                self.subTest(interface=interface),
                patch("mindgarden.interfaces.visit_demo.prepare_demo") as prepare,
                patch("mindgarden.interfaces.local_web.serve_garden", return_value=0) as serve,
            ):
                result = main(["visit", "--local-config", str(config), "--scope", str(scope), *flags])
                self.assertEqual(result, ExitCode.SUCCESS)
                prepare.assert_not_called()
                serve.assert_called_once_with(config.absolute(), scope.absolute(), port=0, demo=False,
                                              interface=interface, assistant="off")

    @unittest.skipUnless(os.name == "posix", "Fictional fixtures use private POSIX controls")
    def test_fixture_scope_leaves_default_authority_unchanged_and_pins_booklet_rows(self):
        from mindgarden.application.booklet import read_booklet_request

        with TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve() / "visit"
            config, scope = prepare_demo(workspace)
            original = scope.read_bytes()
            self.assertFalse(scope.with_name("assistant-scope.json").exists())
            same_config, fixture_scope = prepare_demo(workspace, assistant=True)
            self.assertEqual(same_config, config)
            self.assertNotEqual(fixture_scope, scope)
            self.assertEqual(fixture_scope.stat().st_mode & 0o777, 0o600)
            base = read_object(scope)
            grants = [citation["source"] for citation in read_booklet_request()["sources"]]
            self.assertEqual(len(grants), 8)
            self.assertEqual(read_object(fixture_scope), {
                **base,
                "projections": [*base["projections"], "source-evidence"],
                "source_grants": grants,
            })
            self.assertEqual(scope.read_bytes(), original)
            self.assertEqual(prepare_demo(workspace, assistant=True), (config, fixture_scope))
            self.assertEqual(prepare_demo(workspace), (config, scope))

    @unittest.skipUnless(os.name == "posix", "Fictional fixtures use private POSIX controls")
    def test_fixture_refuses_stale_demo_before_writing_assistant_scope(self):
        with TemporaryDirectory() as temporary:
            workspace = Path(temporary).resolve() / "visit"
            config, scope = prepare_demo(workspace)
            record_path = config.parent / "garden/.garden/knowledge/mock-career.json"
            record = read_object(record_path)
            record_path.write_bytes(canonical_json({**record, "title": "Changed fictional record"}))
            with self.assertRaisesRegex(ContractError, "SESSION_REVISION"):
                prepare_demo(workspace, assistant=True)
            self.assertFalse(scope.with_name("assistant-scope.json").exists())
