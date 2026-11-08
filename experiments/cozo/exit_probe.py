"""Run with python -S to demonstrate core operation without Cozo installed."""

import importlib.util
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from experiments.corpus import create_corpus
from mindgarden.adapters.sqlite_query import SQLiteQueryStore
from mindgarden.application.retrieval import rank

assert importlib.util.find_spec("cozo_embedded") is None
with tempfile.TemporaryDirectory() as tmp:
    corpus = create_corpus(Path(tmp) / "canonical", 1)
    index = corpus["index"]
    context = corpus["context"]
    scope = context.scope_digest()
    store = SQLiteQueryStore(Path(tmp) / "sqlite")
    plan = store.plan(index, scope)
    store.build(index, scope, plan["plan_sha256"], check_live=context.check_live)
    assert store.search(index, scope, "retirement") == rank(index, "retirement")
    assert len(store.search(index, scope, "retirement")) == 2
    assert not store.search(index, scope, "denied-financial-canary")
assert "experiments.cozo.adapter" not in sys.modules
print(
    "PASS: core reference/SQLite rebuild and exact scoped retrieval with Cozo unavailable and experimental adapter unloaded"
)
