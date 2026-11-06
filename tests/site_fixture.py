"""Synthetic reviewed public garden with an explicit replaceable site adapter."""

from pathlib import Path

from mindgarden.domain.site import QUARTZ_COMMIT, QUARTZ_REPOSITORY
from tests.federation_fixture import create_fixture as public_fixture
from tests.support_v1 import write_json


def create_fixture(root: Path, *, empty=False):
    fixture = public_fixture(root)
    profile = fixture["profile"]
    profile.update(kind="site", id="reviewed-public-site", output_root="garden")
    profile["x-site"] = {"schema": "mindgarden.site-adapter/v1", "renderer": "quartz-v5",
                         "repository": QUARTZ_REPOSITORY, "commit": QUARTZ_COMMIT, "node_major": 24,
                         "title": "Synthetic prompt bank", "description": "Reviewed prompts with exact evidence and typed relationships."}
    if empty:
        profile["inputs"] = []
    write_json(fixture["profile_path"], profile)
    fixture["engine"] = fixture["workspace"] / ".cache/mindgarden/quartz"
    return fixture
