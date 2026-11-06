#!/usr/bin/env python3
"""Measure a synthetic optional query cache; observations are not adoption gates."""

from argparse import ArgumentParser
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.adapters.sqlite_query import SQLiteQueryStore, capabilities
from mindgarden.application.retrieval import build_index, rank
from tests.projection_corpus import create_corpus


def benchmark(workspace, count):
    if workspace.exists():
        raise ValueError("Use a new synthetic workspace")
    workspace.mkdir(mode=0o700, parents=True)
    with patch("socket.socket", side_effect=AssertionError("Network attempted")):
        context, _ = create_corpus(workspace, count)
        start = perf_counter()
        index = build_index(context)
        index_seconds = perf_counter() - start
        store = SQLiteQueryStore(workspace / "query-cache")
        scope = context.scope_digest()
        plan = store.plan(index, scope)
        start = perf_counter()
        store.build(index, scope, plan["plan_sha256"], check_live=context.check_live)
        build_seconds = perf_counter() - start
        query = f"needle{count - 1:05d}"
        start = perf_counter()
        reference = rank(index, query)
        reference_seconds = perf_counter() - start
        context.check_live()
        start = perf_counter()
        actual = store.search(index, scope, query)
        sqlite_seconds = perf_counter() - start
        context.check_live()
        assert actual == reference
        result = {
            "schema": "example.query-store-benchmark/1",
            "notes": count,
            "claims": 1,
            "python": platform.python_version(),
            "platform": platform.system(),
            "capabilities": capabilities(),
            "network": "blocked-in-process",
            "parity": "exact",
            "authorized_index_seconds": round(index_seconds, 6),
            "cache_build_seconds": round(build_seconds, 6),
            "reference_rank_seconds": round(reference_seconds, 6),
            "audited_sqlite_search_seconds": round(sqlite_seconds, 6),
            "database_bytes": (workspace / "query-cache/query.sqlite").stat().st_size,
        }
        return result


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--notes", type=int, default=256)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = benchmark(args.workspace.absolute(), args.notes)
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.report:
        with args.report.open("x") as output:
            output.write(content)
    print(content, end="")
