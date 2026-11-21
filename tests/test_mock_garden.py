"""A fictional demo must preserve existing workspaces and authored seed review."""

from copy import deepcopy
import os
from pathlib import Path
import shlex
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import mock_garden_demo as demo
from mindgarden.application.query import QueryContext
from mindgarden.application.retrieval import build_index
from mindgarden.domain.contracts import canonical_json, read_object
from mindgarden.domain.validation import ContractError
from mindgarden.interfaces.visit_demo import prepare_demo


class MockGardenTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "Local browser example uses private POSIX directories")
    def test_browser_seed_retains_fictional_world_and_existing_workspace(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / "visit"
            with patch("socket.socket", side_effect=AssertionError("Network attempted")):
                config, scope = prepare_demo(root)
                context = QueryContext.load(config, scope)
                record_ids = {item["id"] for item in build_index(context)["records"]}
            self.assertEqual(record_ids, set(read_object(demo.SEED / "expected-proof.json")["knowledge_ids"]))
            self.assertIsNone(read_object(scope)["writable"])
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            marker = root / "preserve.txt"
            marker.write_bytes(b"Owned notes remain available")
            before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(prepare_demo(root), (config, scope))
            self.assertEqual({path: path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)

    @unittest.skipUnless(os.name == "posix", "Local browser example uses private POSIX directories")
    def test_browser_seed_refuses_occupied_or_rebound_workspaces(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            marker = root / "keep.txt"
            marker.write_bytes(b"Existing owner content")
            with self.assertRaisesRegex(ContractError, "VISIT_DEMO_WORKSPACE"):
                prepare_demo(root)
            self.assertEqual(list(root.iterdir()), [marker])
            self.assertEqual(marker.read_bytes(), b"Existing owner content")
            workspace = root / "visit"
            config, _ = prepare_demo(workspace)
            bindings = read_object(config)
            bindings["vaults"][0]["root"] = str(root / "unrelated-vault")
            changed = canonical_json(bindings)
            config.write_bytes(changed)
            with self.assertRaisesRegex(ContractError, "VISIT_DEMO_BINDINGS"):
                prepare_demo(workspace)
            self.assertEqual(config.read_bytes(), changed)

    def test_occupied_workspace_is_preserved_before_any_engine_operation(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "keep.txt"
            existing.write_bytes(b"Existing owner content")
            with (
                patch.object(
                    demo, "research_demo", side_effect=AssertionError("Engine called")
                ),
                self.assertRaises(ValueError),
            ):
                demo.workflow(root)
            self.assertEqual(existing.read_bytes(), b"Existing owner content")
            self.assertEqual(list(root.iterdir()), [existing])

    def test_git_location_is_refused_before_creating_output(self):
        with TemporaryDirectory() as temporary:
            parent = Path(temporary)
            (parent / ".git").mkdir()
            output = parent / "new-world"
            with self.assertRaisesRegex(ValueError, "outside Git"):
                demo.workflow(output)
            self.assertFalse(output.exists())

    def test_modified_or_escaping_seed_cannot_reuse_authored_manifest(self):
        world = read_object(demo.SEED / "world.json")
        changed = deepcopy(world)
        changed["entries"][0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "seed changed"):
            demo.sources_for(changed)
        changed = deepcopy(world)
        changed["entries"][0]["file"] = "../outside.txt"
        with self.assertRaises(ContractError):
            demo.sources_for(changed)

    def test_generated_commands_preserve_paths_as_literal_arguments(self):
        root = Path("/var/tmp/fictional folder's example")
        commands = demo.command_examples(
            root / "bindings.json",
            root / "garden",
            root / "session.json",
            root / "request.json",
            root,
        )
        for command in commands.values():
            arguments = shlex.split(command)
            self.assertIn(str(root / "bindings.json"), arguments)
            self.assertIn(str(root / "session.json"), arguments)
