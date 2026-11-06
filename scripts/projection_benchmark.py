#!/usr/bin/env python3
"""Measure bounded synthetic projections; timings are observations, not CI gates."""

from argparse import ArgumentParser
import json
from pathlib import Path
import platform
import sys
from time import perf_counter
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    import mindgarden
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "src"))
    import mindgarden

from mindgarden.application.retrieval import build_index, graph_payload, backlinks_payload, render_context, search_payload
from mindgarden.domain.contracts import canonical_json, digest_bytes
from tests.projection_corpus import create_corpus


def benchmark(workspace, count):
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("Benchmark requires a new or empty synthetic workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    with patch("socket.socket", side_effect=AssertionError("Network attempted")):
        context, profile = create_corpus(workspace, count)
        operations = {"index":lambda:canonical_json(build_index(context)),
                      "search":lambda:canonical_json(search_payload(context, f"needle{count-1:05d}")),
                      "graph":lambda:canonical_json(graph_payload(context, start="synthetic-garden/corpus-00000")),
                      "backlinks":lambda:canonical_json(backlinks_payload(context, "synthetic-garden/corpus-00001")),
                      "context_json":lambda:render_context(context, profile, "json"),
                      "context_markdown":lambda:render_context(context, profile, "markdown")}
        results = {}
        for name, operation in operations.items():
            start = perf_counter(); content = operation(); elapsed = perf_counter() - start
            results[name] = {"seconds":round(elapsed,6), "bytes":len(content), "sha256":digest_bytes(content)}
        if results["context_json"]["bytes"] > profile["max_bytes"] or results["context_markdown"]["bytes"] > profile["max_bytes"]:
            raise AssertionError("Context budget exceeded")
    try:
        import resource
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == "Darwin" else 1024)
    except ImportError:
        peak_rss = None
    budgets = {"max_projection_seconds":60, "max_process_rss_bytes":256 * 1024 * 1024}
    if any(item["seconds"] > budgets["max_projection_seconds"] for item in results.values()) or peak_rss is not None and peak_rss > budgets["max_process_rss_bytes"]:
        raise AssertionError("Synthetic reference performance envelope exceeded")
    return {"reference_budgets":budgets, "budget_status":"passed" if peak_rss is not None else "memory-unavailable", "peak_process_rss_bytes":peak_rss, "platform":platform.system(), "schema":"example.projection-benchmark/1", "python":platform.python_version(), "notes":count,
            "claims":1, "typed_relationships":1, "network":"disabled", "timings":"observed-not-a-performance-guarantee", "operations":results}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--workspace",type=Path,required=True)
    parser.add_argument("--records",type=int,default=1024)
    args = parser.parse_args()
    print(canonical_json(benchmark(args.workspace,args.records)).decode(),end="")
