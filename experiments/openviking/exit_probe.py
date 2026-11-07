"""Run with python -S; core and producer must not require the OpenViking SDK."""

import importlib.util
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from experiments.corpus import create_corpus
from experiments.openviking.adapter import prepare_handoff
from mindgarden.application.retrieval import rank

assert importlib.util.find_spec("openviking") is None
assert importlib.util.find_spec("openviking_sdk") is None
with tempfile.TemporaryDirectory() as tmp:
    corpus = create_corpus(Path(tmp), 1)
    index = corpus["index"]
    selected = [
        r["reference"] for r in index["records"] if r["id"] == "reviewed-prompt"
    ]
    plan, files = prepare_handoff(corpus["context"], selected)
    assert len(plan["entries"]) == 2 and files
    assert len(rank(index, "retirement")) == 2
    assert not rank(index, "denied-financial-canary")
assert "openviking" not in sys.modules and "openviking_sdk" not in sys.modules
print(
    "PASS: scoped reference retrieval and removable producer with OpenViking/SDK unavailable"
)
