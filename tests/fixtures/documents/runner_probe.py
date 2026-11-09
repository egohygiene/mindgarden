"""Synthetic local-reader child group; never reads documents or credentials."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

if sys.argv[1] == "child":
    Path("child-ready").write_text("Synthetic process fixture.\n")
    time.sleep(30)
else:
    child = subprocess.Popen(
        [sys.executable, "-I", "-S", __file__, "child"], stdin=subprocess.DEVNULL
    )
    deadline = time.monotonic() + 0.5
    while not Path("child-ready").exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    Path("probe-state.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "child_pid": child.pid,
                "group": os.getpgrp(),
                "cwd": os.getcwd(),
                "environment": dict(os.environ),
            }
        )
    )
    if sys.argv[1] == "timeout":
        time.sleep(30)
