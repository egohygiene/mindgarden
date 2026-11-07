# Learning and optional-system evaluation checkpoints

The maintainer selected #28 → #21 → #26 → #33 → #34 for an overnight batch,
then a morning sync. This is implementation/evaluation authority for bounded
reviewable drafts, not merge, publication, release or ADR-ratification authority.
The combined checkout extends draft #104 (`0d436f49af1a8593676f7c77451c93dbc34b543f`)
and preserves #93–#104. Main remains `d5edb13`; all 44 issues remain open.

## Dependency reconciliation before implementation

- #28 authored candidate, private review history, deterministic exports and
  replaceable scheduling use the existing #12/#13/#31 services. Full #17 web
  adoption and Realm #20 runtime are later integration proofs. A static accessible
  study document is a disposable adapter, not a new web application framework.
- #21 says post-1.0 and lists #19. The maintainer explicitly selected its bounded
  candidate work now while deferring releases. Treat that as a scheduling change
  for the producer schema/fixture/export checkpoint. Publishing, downstream
  consumer acceptance and release acceptance remain separate; do not silently
  reinterpret the release gate as complete.
- #26 is an architectural evaluation, independent of deploying OpenAleph.
  Inspect exact official source/release/license and distinguish useful patterns
  from dependency or service adoption. No real data or production service.
- #33/#34 follow the available optional #32 port/reference/SQLite checkpoint.
  #26 supplies evaluation framing, not a new mandatory service. Realm #25 and
  Aether capability work remain gates for confidential/runtime/agent assurance;
  an ordinary offline synthetic experiment cannot satisfy those contracts.
- #46 retention separates originals, canonical knowledge, learning/memory views
  and publication. Review history is private. No source deletion or knowledge
  promotion follows from grading, compaction or generated artifacts.

These corrections are recorded for review. Existing proposed ADRs remain
proposed; the evaluations may recommend adapt/defer/reject without adopting any
new default store, framework, model provider or product.

## Checkpoint ledger

| Issue | Branch / PR and implemented checkpoint | Verification | Remaining / exact next action |
| --- | --- | --- | --- |
| #28 | [draft #105](https://github.com/egohygiene/mindgarden/pull/105), `3510b22`, over #104; authored cards/summaries/private grading/versioned schedules/export round trip | 12 focused tests on Python 3.12/3.13 + 5 schema tests; Chromium static accessibility proof | Full hosted #17 study UI, reminders/sync and runtime assurance; optional automatic proposals; review #105 |
| #21 | [draft #106](https://github.com/egohygiene/mindgarden/pull/106), `4e12dcd`, over #105; public reviewed candidates/series, rights, duplicates and artifact-feedback projections | 9 focused tests on Python 3.12/3.13 + 5 schema cases | Approved private redaction and accepted downstream intake/publication remain open; review #106 |
| #26 | [draft #107](https://github.com/egohygiene/mindgarden/pull/107), `c5b1f52`, over #106; [pinned architecture/privacy/cost/ownership matrix](evaluations/openaleph.md), proposed adapt/defer recommendation | Official 5.3.2 source/license/docs reviewed; native FtM binary probe blocked, not passed | Maintainer disposition; optional native FtM export blocked by PyICU/ICU; no service adoption |
| #33 | [draft #108](https://github.com/egohygiene/mindgarden/pull/108), `7c75d12`, over #107; [native adapter/measurements/recovery/exit](evaluations/cozodb.md), proposed defer adoption | Five native cases; 262-record exact parity; native FTS/HNSW smoke; no-Cozo exit probe | Maintainer disposition, other platforms, actual upgrades, installed restore dispatch and confidential runtime remain open |
| #34 | [draft #109](https://github.com/egohygiene/mindgarden/pull/109), `e410be7`, over #108; [producer/native blocked-runtime evaluation](evaluations/openviking.md), proposed adapt/defer | Four producer cases on Python 3.12/3.13; native 0.5.3/SDK 0.1.18 config/model/network/startup observations, explicitly blocked | Native quality/retrieval/memory/backup/upgrade/encrypted-runtime proofs blocked; review proposed defer disposition |

## Existing gates retained

Draft #104's exact-head engine Test 42314280753 and release-preparation check
42314280811 pass. Decisions preview 42314281186 fails; its earlier native
source-validation finding remains #43's gate. #41 historical migration and #47
full framework/runtime work remain gated. Real #20 pilot/consumer cutover,
restricted runtime assurance and #48 external handoffs remain unverified.
Release #19, further release work and deferred #86–#91 are not activated.

The exact next action is morning maintainer review of #105 → #106 → #107 → #108 → #109. No automatic merge. Every
checkpoint will record source/PR, commands/results, supported interfaces, genuine
blockers and the following action. Leave all new drafts for the morning sync.

## Reproducible validation of the combined stack

`python -S scripts/learning_insight_demo.py --require-source` proves exact
committed learning/insight goldens through CLI preview/apply and learning import.
Run with an isolated installed wheel using `python -I ... --require-installed`
for the packaging proof. Parent/CLI Python sockets are blocked; only temporary
synthetic fixtures are accepted. Optional native experiment commands, limits
and blocked steps are recorded in their linked evaluations. The [combined verification receipt](evaluations/batch-verification-2026-11-07.json)
records the exact functional source, local suite results, build hashes and
limits. Evaluation scripts/locks are a repository-only lab: run them from a
Git checkout, separately from the installed core package.


## Final functional-source receipt

Combined functional source: `e410be7bebc865d3b7d0b684ec65b470d14940a9` on
`experiment/34-openviking-projection`. Reproduce the entire stack by checking out
that full commit or the later documentation-only receipt on the same branch.
New drafts remain over #104; no merge is authorized by this handoff.

| Command / environment | Actual result |
| --- | --- |
| `.venv/bin/python -m unittest discover --start-directory tests --verbose` | **381 pass**, no skips; Python 3.12.14, 321.205 s |
| `.cache/python313/bin/python -m unittest discover --start-directory tests --verbose` | **381 pass**, no skips; Python 3.13.5, 301.556 s |
| `python3 scripts/learning_browser_check.py --report tests/fixtures/learning/observed-browser.json` | Chromium 151 / Playwright 1.62; native keyboard disclosure, 320/1280 px, 200% zoom, reduced motion pass; static adapter only |
| `.cache/evaluations/cozo-python/bin/python -m unittest experiments.cozo.test_adapter -q` | Five real native cases pass; same abi3 wheel also passes five on Python 3.13 (9.862 s final run) |
| `.venv/bin/python -m unittest experiments.openviking.test_adapter -q` and Python 3.13 equivalent | Four producer cases pass on each; **not** native service acceptance |
| `python -S -m experiments.cozo.exit_probe` / `experiments.openviking.exit_probe` | Both core/producer paths pass without optional packages; also pass from clean archived source |
| `python -S scripts/learning_insight_demo.py --require-source` | Exact authored golden hashes, CLI preview/apply and learning import pass from clean `git archive e410be7` |
| `python -I scripts/learning_insight_demo.py --require-installed` | Same goldens pass from an isolated wheel built from that clean archive; no source fallback |
| `python -S/-I scripts/product_checkpoint_demo.py --require-source/--require-installed` | Existing memory/dependency/SQLite/private-bookmark proof passes in clean source and installed modes; external Akashic handoff remains unavailable |
| `../../../.venv/bin/python -m build --no-isolation --outdir ../dist-clean` in `.cache/evaluations/clean-final` | sdist/wheel build pass; wheel includes all 14 new contracts, no experimental runtime dependencies |
| Pinned owner checks, focused Ruff `--select F,E9`, formatting and `git diff --check` | Pass; 44 unique coverage rows, all ADRs proposed/null approval, continuity within bounds; 100 changed-document relative links resolve |

The first full runs each had **one error** because the default sandbox disallows
the existing preview test's loopback socket. The complete reruns above used
network permission and passed; the denial is not suppressed or counted as a
passing test. Core suite evidence does not include the optional native lab.

The exact Python 3.13 Cozo invocation used the already isolated abi3 artifact:

```sh
.cache/python313/bin/python - <<'PYTHON'
import sys, unittest
sys.path.insert(0, ".cache/evaluations/cozo-python/lib/python3.12/site-packages")
suite = unittest.defaultTestLoader.loadTestsFromName("experiments.cozo.test_adapter")
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(not result.wasSuccessful())
PYTHON
```

Hosted observations are separate from local results. Automatic Test and release
preparation checks passed at #105 `5e31428` (42350823888/42350823974), #106
`8e2ff53` (42351178215/42351178194), #107 `c0a0cd7`
(42351334067/42351334041), and #108 `169ded0`
(42351990116/42351990107). At #109 functional `e410be7`, release-preparation
42352829972 passed and Test 42352829961 was running at this observation.
Documentation receipts create their own later runs; pending is not passing.
No paid/manual workflow was launched. The earlier **failed Decisions preview
42314281186** remains an unresolved source-validation gate.

Morning action: review #105 → #106 → #107 → #108 → #109 after the existing
#93–#104 stack; decide the proposed evaluation dispositions and select the next
ready parent gaps. Keep #19 releases, #86–#91, full private pilots and any
unapproved runtime/publication work parked.
