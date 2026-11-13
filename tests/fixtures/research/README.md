# Synthetic research clients

`search-first.json` and `graph-first.json` are distinguishable data-only caller
plans over `tests/research_fixture.py`. They are not live-model outputs. They
exercise the existing seven scoped read handlers and retain an instruction-bearing
source strictly as data. Tests also remove the planner/provider dependency and
use direct search without model calls.

`expected-proof.json` is the complete `scripts/research_demo.py` golden: two
synthetic Drive captures, the reviewed ledger packet, search/context/evidence,
relocation/restore/clean rebuild, three CLI client results and metadata-only
pilot readiness. No account, Codex runtime, model quality or real pilot is claimed.
Initial development errors and corrected qualification are recorded in the local
workflow ledger rather than treated as passing evidence.
