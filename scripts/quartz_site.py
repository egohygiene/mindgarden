#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Compatibility entry point for ``mindgarden site``."""

from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).parents[1] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from mindgarden.adapters.quartz import *  # noqa: E402,F403
from mindgarden.adapters.quartz import main as _main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(_main())
