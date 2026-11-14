#!/usr/bin/env python3
"""Measure a synthetic optional query cache; observations are not adoption gates."""

from argparse import ArgumentParser
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
import tracemalloc
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from mindgarden.adapters.sqlite_query import SQLiteQueryStore, capabilities
from mindgarden.application.retrieval import build_index, rank
from tests.projection_corpus import create_corpus
from tests.support_v1 import write_json
from mindgarden.application.query import QueryContext
from mindgarden.application.sessions import bind_session_revisions
from mindgarden.domain.contracts import read_object


def benchmark(workspace, count, *, refresh=False):
    if workspace.exists():
        raise ValueError("Use a new synthetic workspace")
    workspace.mkdir(mode=0o700, parents=True)
    tracemalloc.start()
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
        if refresh:
            path = (
                workspace / "garden/.garden/knowledge" / f"corpus-{count - 1:05d}.json"
            )
            record = read_object(path)
            record["title"] = "Refreshed synthetic procedure"
            write_json(path, record)
            write_json(
                context.session_path,
                bind_session_revisions(context.bindings.path, context.session),
            )
            current = QueryContext.load(context.bindings.path, context.session_path)
            start = perf_counter()
            refreshed = build_index(current)
            current_index_seconds = perf_counter() - start
            start = perf_counter()
            plan = store.refresh_plan(refreshed, current.scope_digest())
            plan_seconds = perf_counter() - start
            start = perf_counter()
            store.refresh(
                refreshed,
                current.scope_digest(),
                plan["plan_sha256"],
                check_live=current.check_live,
            )
            refresh_seconds = perf_counter() - start
            assert store.search(refreshed, current.scope_digest(), "refreshed") == rank(
                refreshed, "refreshed"
            )
            assert store.load(refreshed, current.scope_digest()) == refreshed
            result["refresh"] = {
                "changed_records": 1,
                "current_authorized_index_seconds": round(current_index_seconds, 6),
                "review_plan_seconds": round(plan_seconds, 6),
                "apply_seconds": round(refresh_seconds, 6),
                "authority": "renewed-exact-session",
                "parity": "exact",
            }
        result["peak_python_allocated_bytes"] = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        return result


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--notes", type=int, default=256)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Also measure one canonical metadata change under renewed authority",
    )
    args = parser.parse_args()
    result = benchmark(args.workspace.absolute(), args.notes, refresh=args.refresh)
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.report:
        with args.report.open("x") as output:
            output.write(content)
    print(content, end="")
