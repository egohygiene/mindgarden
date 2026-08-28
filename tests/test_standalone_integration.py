# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT
# pylint: disable=wrong-import-position

from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

MINDGARDEN_ROOT = Path(__file__).parents[1]
FIXTURE_ROOT = MINDGARDEN_ROOT / "tests/fixtures/public-garden"
sys.path.insert(0, str(MINDGARDEN_ROOT))

from scripts.garden_agent import (  # noqa: E402
    build_index,
    canonical_json,
    load_context_pack,
    render_context_markdown,
    render_llms_txt,
    search_payload,
)
from scripts.publish_garden import project_garden, projection_digests  # noqa: E402
from scripts.quartz_site import cache_path  # noqa: E402
from scripts.validate_garden import ContractError, validate_repository  # noqa: E402


class StandaloneIntegrationTests(unittest.TestCase):
    def test_fixture_exercises_contract_index_search_and_context(self) -> None:
        self.assertEqual(validate_repository(FIXTURE_ROOT), 3)
        first = canonical_json(build_index(FIXTURE_ROOT))
        second = canonical_json(build_index(FIXTURE_ROOT))
        self.assertEqual(first, second)

        index = json.loads(first)
        reviewed = search_payload(
            index,
            "architecture",
            limit=10,
            include_unreviewed=False,
        )
        self.assertNotIn(
            "public-garden-draft",
            {result["id"] for result in reviewed["results"]},
        )

        _, profile = load_context_pack(FIXTURE_ROOT, "public-garden-default")
        context = render_context_markdown(FIXTURE_ROOT, index, profile)
        self.assertIn("public-garden-architecture", context)
        self.assertNotIn("public-garden-draft", context)
        self.assertLessEqual(len(context), profile["max_characters"])

        llms = render_llms_txt(FIXTURE_ROOT, index)
        self.assertEqual(
            (FIXTURE_ROOT / "llms.txt").read_text(encoding="utf8"),
            llms,
        )
        self.assertIn("https://github.com/egohygiene/mindgarden/", llms)
        self.assertNotIn("mindgarden/scripts", llms)

    def test_fixture_projects_with_consumer_owned_default_profile(self) -> None:
        with (
            TemporaryDirectory() as first_directory,
            TemporaryDirectory() as second_directory,
        ):
            first = Path(first_directory) / "site"
            second = Path(second_directory) / "site"
            first_paths = project_garden(FIXTURE_ROOT, first)
            second_paths = project_garden(FIXTURE_ROOT, second)

            self.assertEqual(first_paths, second_paths)
            self.assertEqual(projection_digests(first), projection_digests(second))
            self.assertEqual(
                [path.as_posix() for path in first_paths],
                ["concepts/architecture.md", "index.md"],
            )
            self.assertFalse((first / "concepts/draft.md").exists())

    def test_obsidian_and_quartz_profiles_are_standalone(self) -> None:
        obsidian = json.loads(
            (MINDGARDEN_ROOT / "profiles/obsidian/profile.json").read_text(
                encoding="utf8"
            )
        )
        self.assertEqual(obsidian["schema"], "mindgarden.obsidian-profile/v0")
        self.assertEqual(obsidian["vaultRoot"], ".")
        self.assertEqual(obsidian["requiredCommunityPlugins"], [])

        quartz = (MINDGARDEN_ROOT / "profiles/quartz/quartz.config.yaml").read_text(
            encoding="utf8"
        )
        self.assertIn("Example Mindgarden", quartz)
        self.assertNotIn("egohygiene/empathy", quartz)

    def test_quartz_cache_cannot_escape_consumer_repository(self) -> None:
        with TemporaryDirectory() as directory:
            repository = Path(directory)
            self.assertEqual(
                cache_path(repository, Path(".cache/mindgarden/site"), "site"),
                (repository / ".cache/mindgarden/site").resolve(),
            )
            with self.assertRaisesRegex(ContractError, "must stay beneath"):
                cache_path(repository, Path("outside"), "site")


if __name__ == "__main__":
    unittest.main()
