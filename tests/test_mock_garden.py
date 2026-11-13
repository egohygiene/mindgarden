"""A fictional demo must preserve existing workspaces and authored seed review."""

from copy import deepcopy
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
from mindgarden.domain.contracts import read_object
from mindgarden.domain.validation import ContractError


class MockGardenTests(unittest.TestCase):
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
