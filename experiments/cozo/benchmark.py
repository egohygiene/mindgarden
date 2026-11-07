"""Isolated-process observation, not a production throughput claim."""

import argparse
import json
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from mindgarden.application.retrieval import rank
from mindgarden.domain.contracts import canonical_json, digest_bytes

QUERIES = (
    "prompt",
    "retirement",
    "café long-term",
    "canonical home",
    "日本語",
    "NOT OR *",
)


def worker(arguments):
    index = json.loads(arguments.index.read_text())
    scope = index["scope_sha256"]
    started = time.perf_counter()
    if arguments.worker == "cozo":
        from experiments.cozo.adapter import CozoQueryStore

        store = CozoQueryStore(arguments.cache)
    elif arguments.worker == "sqlite":
        from mindgarden.adapters.sqlite_query import SQLiteQueryStore

        store = SQLiteQueryStore(arguments.cache)
    else:
        store = None
    import_ms = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    if store:
        p = store.plan(index, scope)
        store.build(index, scope, p["plan_sha256"], check_live=lambda: None)
    build_ms = (time.perf_counter() - started) * 1000
    timings = []
    fingerprints = {}
    for _ in range(5):
        for query in QUERIES:
            started = time.perf_counter()
            results = store.search(index, scope, query) if store else rank(index, query)
            timings.append((time.perf_counter() - started) * 1000)
            assert results == rank(index, query)
            fingerprints[query] = digest_bytes(canonical_json(results))
    result = {
        "adapter": arguments.worker,
        "import_ms": round(import_ms, 3),
        "build_ms": round(build_ms, 3),
        "query_median_ms": round(statistics.median(timings), 3),
        "query_p95_ms": round(sorted(timings)[int(0.95 * (len(timings) - 1))], 3),
        "queries": len(timings),
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "cache_bytes": sum(
            p.stat().st_size for p in arguments.cache.rglob("*") if p.is_file()
        )
        if store
        else 0,
        "result_fingerprints": fingerprints,
    }
    if store:
        before = time.perf_counter()
        backup = store.backup(index, scope)
        result["portable_backup_bytes"] = len(canonical_json(backup))
        result["backup_ms"] = round((time.perf_counter() - before) * 1000, 3)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-per-garden", type=int, default=128)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--worker", choices=["reference", "sqlite", "cozo"])
    parser.add_argument("--index", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    if not 1 <= args.records_per_garden <= 512:
        parser.error("bounded synthetic corpus requires 1..512 records per garden")
    from experiments.corpus import create_corpus

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        started = time.perf_counter()
        corpus = create_corpus(root / "corpus", args.records_per_garden)
        preparation_ms = (time.perf_counter() - started) * 1000
        index = corpus["index"]
        path = root / "index.json"
        path.write_bytes(canonical_json(index))
        observations = []
        for adapter in ("reference", "sqlite", "cozo"):
            output = subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "experiments.cozo.benchmark",
                    "--worker",
                    adapter,
                    "--index",
                    str(path),
                    "--cache",
                    str(root / adapter),
                ],
                text=True,
            )
            observations.append(json.loads(output))
        assert all(
            o["result_fingerprints"] == observations[0]["result_fingerprints"]
            for o in observations
        )
        report = {
            "schema": "mindgarden.cozo-observation/v1",
            "observed_at": "2026-11-07",
            "python": platform.python_version(),
            "platform": platform.system() + "/" + platform.machine(),
            "records": len(index["records"]),
            "gardens": 2,
            "excluded_personal_records": 1,
            "typed_edges": len(index["edges"]),
            "index_bytes": path.stat().st_size,
            "synthetic_corpus_prepare_ms": round(preparation_ms, 3),
            "queries": list(QUERIES),
            "observations": observations,
            "parity": "exact results, scores, reasons and source references",
            "network": "execution in default network-denied sandbox; native trace recorded separately",
            "limitations": [
                "Small synthetic corpus; no production throughput, semantic quality or confidential-runtime assurance.",
                "Each query includes full cache checksum/relation audit for both durable stores.",
                "Per-worker peak RSS includes interpreter/module/index initialization; installation footprint is separate.",
                "No incremental writes, vectors, native FTS ranking or multi-writer support in the adapter.",
            ],
        }
        content = canonical_json(report)
        if args.report:
            args.report.write_bytes(content)
        print(content.decode(), end="")


if __name__ == "__main__":
    main()
