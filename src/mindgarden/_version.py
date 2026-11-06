"""Derive runtime version from PEP 621 source metadata or installed distribution metadata."""

from importlib.metadata import version
from pathlib import Path
import tomllib


def package_version() -> str:
    project = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if Path(__file__).resolve().parent.parent.name == "src" and project.is_file():
        metadata = tomllib.loads(project.read_text(encoding="utf8"))["project"]
        if metadata["name"] == "mindgarden":
            return metadata["version"]
    return version("mindgarden")


__version__ = package_version()
