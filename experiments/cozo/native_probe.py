"""Separate synthetic native FTS/vector and backup features, not Garden semantics."""

import argparse
from contextlib import closing
import importlib.metadata
import json
from pathlib import Path

from cozo_embedded import CozoDbPy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    with closing(CozoDbPy("mem", "", "{}")) as db:
        db.run_script(":create docs {id: String => body: String}", {}, False)
        db.run_script(
            "?[id,body] <- [['a','exact world evidence'],['b','world context']] :put docs {id => body}",
            {},
            False,
        )
        db.run_script(
            "::fts create docs:fts {extractor: body, tokenizer: Simple, filters: [Lowercase]}",
            {},
            False,
        )
        fts = db.run_script("?[id] := ~docs:fts{id | query: 'world', k: 2}", {}, True)[
            "rows"
        ]
        assert sorted(fts) == [["a"], ["b"]]
        db.run_script(":create vectors {id: String => v: <F32; 2>}", {}, False)
        db.run_script(
            "?[id,v] <- [['near',[1,1]],['far',[10,10]]] :put vectors {id => v}",
            {},
            False,
        )
        db.run_script(
            "::hnsw create vectors:knn {dim: 2, m: 16, dtype: F32, fields: [v], distance: L2, ef_construction: 20}",
            {},
            False,
        )
        nearest = db.run_script(
            "?[id] := ~vectors:knn{id | query: q, k: 1, ef: 20}, q = vec([1,1])",
            {},
            True,
        )["rows"]
        assert nearest == [["near"]]
    result = {
        "schema": "mindgarden.cozo-native-probe/v1",
        "native_version": importlib.metadata.version("cozo-embedded"),
        "fts": {
            "matched_ids": [r[0] for r in sorted(fts)],
            "ranking_parity_claim": False,
        },
        "vector": {
            "dimensions": 2,
            "nearest_id": nearest[0][0],
            "model_calls": 0,
            "semantic_quality_claim": False,
        },
        "default_adapter_vectors": False,
        "network_required": False,
    }
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.report:
        args.report.write_text(content)
    print(content, end="")


if __name__ == "__main__":
    main()
