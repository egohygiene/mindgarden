"""Synthetic-only fixtures for portable v1 application conformance."""

from pathlib import Path
import json

from mindgarden.application.lifecycle import GardenIdentity, apply_init, build_init_plan
from mindgarden.domain.contracts import canonical_json, digest_bytes

FIXTURES = Path(__file__).parent / "fixtures/contracts/v1/valid"
TIME = "2026-11-04T00:00:00Z"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(value))


def reference(garden: str, record_id: str, digest: str | None = None) -> dict:
    return {"garden": garden, "id": record_id,
            "revision": "sha256:" + digest if digest else None}


def create_garden(root: Path, garden_id: str = "synthetic-garden", visibility: str = "private") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    identity = GardenIdentity(garden_id, "Synthetic garden", "personal", visibility,
                              ("synthetic-owner",), "urn:mindgarden:garden:" + garden_id,
                              None, ("knowledge-systems",), ("prompt-bank",))
    apply_init(root, build_init_plan(identity))
    return root / ".garden"


def add_knowledge(root: Path, record_id: str = "synthetic-prompt", body: str = "Use exact source evidence.\n",
                  *, visibility: str = "private", reviewed: bool = True, sources: list | None = None) -> dict:
    garden = root / ".garden"
    garden_id = json.loads((garden / "garden.json").read_text())["id"]
    record = json.loads((FIXTURES / "knowledge-reviewed-public.json").read_text())
    content = body.encode("utf8")
    record.update(id=record_id, garden=garden_id, title="Synthetic prompt bank entry", kind="procedure",
                  visibility=visibility, authors=[{"kind": "human", "id": "synthetic-author"}],
                  created="2026-11-04", updated="2026-11-04", domains=["knowledge-systems"],
                  topics=["prompt-bank"], tags=[], claims=[], synapses=[], sources=sources or [],
                  publication="excluded", content={"path": f"knowledge/{record_id}.md",
                                                     "sha256": digest_bytes(content)})
    record["review"] = ({"state": "approved", "reviewers": ["synthetic-reviewer"],
                          "reviewed_at": TIME, "rationale": "Synthetic human review fixture."}
                         if reviewed else {"state": "unreviewed", "reviewers": [],
                                           "reviewed_at": None, "rationale": None})
    record["status"] = "active" if reviewed else "proposed"
    provenance = json.loads((FIXTURES / "provenance.json").read_text())
    provenance.update(id="provenance-" + record_id, garden=garden_id,
                      artifact=reference(garden_id, record_id, digest_bytes(content)),
                      artifact_sha256=digest_bytes(content), inputs=[], origin=None,
                      created_at=TIME, rights="Synthetic authored material.")
    record["provenance"] = [reference(garden_id, provenance["id"], digest_bytes(canonical_json(provenance)))]
    (garden / record["content"]["path"]).write_bytes(content)
    write_json(garden / f"provenance/{provenance['id']}.json", provenance)
    write_json(garden / f"knowledge/{record_id}.json", record)
    return record
