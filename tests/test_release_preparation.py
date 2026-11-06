"""Version authority and adversarial release artifact checks, without publication."""

import io
from pathlib import Path
import sys
import tarfile
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

import mindgarden
import mindgarden._version as runtime_version
from scripts import release


class ReleasePreparationTests(unittest.TestCase):
    def temporary(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def test_source_runtime_version_uses_the_declared_authority(self):
        self.assertEqual(mindgarden.__version__, tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"])
        with patch("scripts.release.require_tool", side_effect=AssertionError("Owner tools opened before version decision")):
            with self.assertRaisesRegex(release.ReleaseError, "RELEASE_VERSION_DRIFT"):
                release.qualified_plan(ROOT, Path("unused"), "v9.9.9")

    def test_runtime_version_follows_a_changed_source_manifest(self):
        root = self.temporary(); module = root / "src/mindgarden/_version.py"; module.parent.mkdir(parents=True)
        (root / "pyproject.toml").write_text('[project]\nname = "mindgarden"\nversion = "2.3.4"\n')
        with patch.object(runtime_version, "__file__", str(module)):
            self.assertEqual(runtime_version.package_version(), "2.3.4")

    def test_existing_destination_is_preserved_before_any_build(self):
        root = self.temporary(); target = root / "human"; target.mkdir()
        marker = target / "retain.txt"; marker.write_text("Synthetic user-owned file.\n")
        with patch("scripts.release.build_once", side_effect=AssertionError("Build entered before destination check")):
            with self.assertRaisesRegex(release.ReleaseError, "RELEASE_DESTINATION"):
                release.prepare(ROOT, root, target)
        self.assertEqual(marker.read_text(), "Synthetic user-owned file.\n")

    def test_candidate_cannot_be_created_inside_canonical_storage(self):
        root = self.temporary(); (root / ".garden").mkdir()
        (root / ".garden/garden.json").write_text("Synthetic canonical boundary marker")
        with self.assertRaisesRegex(release.ReleaseError, "RELEASE_DESTINATION"):
            release.prepare(ROOT, root, root / "new-candidate")
        self.assertFalse((root / "new-candidate").exists())

    def test_unsafe_source_links_are_denied_before_extraction(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            member = tarfile.TarInfo("unsafe"); member.type = tarfile.SYMTYPE; member.linkname = "../../outside"
            archive.addfile(member)
        with tarfile.open(fileobj=io.BytesIO(raw.getvalue())) as archive:
            with self.assertRaisesRegex(release.ReleaseError, "RELEASE_ARCHIVE"): release.safe_members(archive)

    def test_sdist_normalization_removes_host_time_owner_and_order_variance(self):
        root = self.temporary(); first = root / "first.tar.gz"; second = root / "second.tar.gz"
        for destination, order, timestamp in [(first, ["b.txt", "a.txt"], 1), (second, ["a.txt", "b.txt"], 2)]:
            with tarfile.open(destination, "w:gz") as archive:
                for name in order:
                    content = ("Synthetic " + name).encode()
                    member = tarfile.TarInfo(name); member.size = len(content); member.uid = timestamp; member.mtime = timestamp
                    archive.addfile(member, io.BytesIO(content))
            release.normalize_sdist(destination, 1794000000)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with tarfile.open(first, "r:gz") as archive:
            self.assertEqual(archive.extractfile("a.txt").read(), b"Synthetic a.txt")

    def test_wheel_normalization_preserves_member_bytes_and_determinism(self):
        root = self.temporary(); paths = [root / "first.whl", root / "second.whl"]
        for number, destination in enumerate(paths):
            with zipfile.ZipFile(destination, "w") as archive:
                for name in (["b", "a"] if number else ["a", "b"]):
                    archive.writestr(name, "Synthetic " + name)
            release.normalize_wheel(destination, 1794000000)
        self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
        with zipfile.ZipFile(paths[0]) as archive: self.assertEqual(archive.read("a"), b"Synthetic a")
