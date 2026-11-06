# Private policy and storage sprint — 2026-11-06

The maintainer authorized #29 → #31 → #30 → #35 → #45 as additional small draft
checkpoints on top of #79. Main remains `30a2966`; #74–#79 remain draft/unmerged.
The previous combined base is `8e15314cb3419b1defaf1866aa6450d6703abb09`, whose
final automatic Test run 42177086645 passed. No merge or ADR approval is inferred.

## Dependencies and bounded scope

#29 supplies the shared local decision contract before #31 consumes it across
outputs. #30 reuses #31's owned cache inventory, without making native Windows
assurance a prerequisite for the Linux baseline. #35 consumes #11's source adapter
boundary and #29 policy; PDF acquisition, optional parser tools and model calls
remain separate. #45 consumes the PDF/media evidence and registry bindings for
mixed-source recovery. Full encrypted/runtime/provider proofs are later integration
requirements, not claims supplied by a filesystem flag.

Hygiene #39/#40 remain open with no comments. The inspected Hygiene main is
`92195e49b50778517ef670a7ec97c922dbdf9cec`; no normative classification/assurance
artifact was found under the referenced schema/spec/document paths. The existing
local policy is therefore still a proposed reference implementation, not adopted
organization policy. Realm #25 is an open program; its handoff directs current
remaining acceptance to #60, including encrypted-vault/key-broker and confidential
runtime proofs. Unknown policy and unproved restricted runtime fail closed.

A newly supplied ordinary or synthetic PDF may have an explicit digest-bound
initial classification review; a previously restricted source is never silently
reclassified. Default confidential processing must remain unavailable until its
external contracts and actual runtime/storage evidence exist. Real personal,
employment, business and provider data are out of scope.

| Issue | Checkpoint | Remaining acceptance | Draft / branch | Verification | Next action |
| --- | --- | --- | --- | --- | --- |
| #29 | Shared decision schema/API/CLI over existing scope model; policy adoption gaps explicit | Accepted Hygiene/Realm integration and declassification protocol | [#80](https://github.com/egohygiene/mindgarden/pull/80); `feature/29-policy-integration` over #79; `9fc0c9b` | 25 policy/scoped/contracts on 3.12; 5 policy on 3.13 | Review #80; #31 follows |
| #31 | Output-wide authorization/budgets/diagnostics and owned cache inventories | External assurance and broader runtime/provider matrices | [#81](https://github.com/egohygiene/mindgarden/pull/81); `feature/31-output-scope-enforcement` over #80; `1bbb38f` | 25 output/scoped/contracts on 3.12; 5 output on 3.13 | Review #81; #30 follows |
| #30 | Platform capability matrix, registry recovery and reversible owned cache handling | Native platform/ACL and encrypted host acceptance | [#82](https://github.com/egohygiene/mindgarden/pull/82); `feature/30-registry-cache-recovery` over #81; `9b8e008` | 39 registry/cache/contracts on 3.12; 5 cache recovery on 3.13 | Review #82; #35 follows |
| #35 | Versioned document bundle, optional local PDF reader and exact page/span evidence | Restricted runtime, OCR/office adapters and real consumer proof | [#83](https://github.com/egohygiene/mindgarden/pull/83); `feature/35-local-document-adapter` over #82; `e966e3e` | 20 PDF/adapter/contracts on 3.12; 8 PDF on 3.13; real Poppler 25.03.0 six-state proof | Review #83; #45 follows |
| #45 | Mixed archive/document/media inventory, triage and recovery proof | Encrypted/provider/platform integration and destructive GC | [#84](https://github.com/egohygiene/mindgarden/pull/84); `feature/45-mixed-source-vault-proof` over #83; `79e39f0` | Real/recorded mixed golden; clean source/wheel; 298 tests on each supported Python; exact verification below | Review #74–#84 in order; disposition external contracts separately |

## Review and recovery

Every checkpoint records the functional source, branch/base/PR, exact commands and
results, blockers and next action here and in CONTINUITY.md. Later drafts name the
preceding branch as their base. Keep all drafts unmerged for maintainer review,
retain every parent criterion, and distinguish implementation, testing and owner
acceptance. The final branch will preserve the complete combined checkout.

## Combined functional source and exact verification

The reproducible combined functional checkout is
`79e39f072c249760e20fd567f679395f37931816` on
`feature/45-mixed-source-vault-proof`. It contains #74–#84, with each draft based
on the preceding branch. The follow-up documentation/handoff commit does not
change engine, schemas or fixtures. A refreshed live inventory still has 38 open
parent issues and eleven open drafts (#74–#84); nothing was merged or closed.

| Command | Observed result |
| --- | --- |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist` | Fresh source/wheel built from the functional tree; no runtime dependencies |
| `.venv/bin/python -m unittest discover --start-directory tests --verbose` | **298 passed**, no skips; Python 3.12.14; 241.911 s |
| `.cache/python313/bin/python -m unittest discover --start-directory tests --verbose` | **298 passed**, no skips; Python 3.13.5; 230.781 s |
| `.venv/bin/python -m unittest tests.test_registry_cache tests.test_documents tests.test_assets tests.test_storage_adapters -q` | 27 passed, including the final interrupted-restore and classification-authority regressions |
| `.venv/bin/python -m unittest tests.test_distribution -q` | 2 passed against fresh artifacts, including new modules/contracts and synthetic binary fixtures |
| `.venv/bin/python scripts/mixed_vault_demo.py --workspace .cache/mixed-real-proof --tool-directory /usr/bin --require-source --report .cache/mixed-real-proof.json` | Real Poppler 25.03.0; complete mixed golden passes with explicit real-reader mode |
| `.venv/bin/python scripts/document_demo.py --workspace .cache/pdf-final-proof --tool-directory /usr/bin --require-source --report .cache/pdf-final-proof.json` | Six real parser states, exact page layout, repeat import, original preservation and removed scratch pass |
| `.venv/bin/python -m compileall -q src scripts tests` | Passed |
| `python3 .cache/six_owner_checks.py` | All indexed ADRs proposed/null approval; pinned Hygiene policy/schema/set/index; pinned Aether continuity/12 headings/size; 38 unique ledger rows pass |
| `git diff --check`; changed Markdown relative-link check | Passed |
| `node --version` | v24.19.0 |

The local owner-check orchestration uses unchanged pinned Hygiene
`a05b14f8b9e2772124f879f818e09a911e996ad8` and Aether
`b7597301c4d22a9bcd580967b5753138bb368111` validators. Its commands and assertions
are described by the existing owner/continuity process; the helper itself is
local orchestration, not a new owner contract. No paid workflow was dispatched.

### Clean source and isolated installed engine

These exact commands passed from the functional snapshot. Both JSON reports
match the committed mixed-vault golden byte for byte. The installed PDF proof
also passes with real native tools; installed metadata has no `Requires-Dist`.
All workspaces are disposable synthetic fixtures.

```bash
mkdir .cache/storage-clean-checkout
git archive 79e39f072c249760e20fd567f679395f37931816 | \
  tar --extract --directory .cache/storage-clean-checkout
PYTHONPATH=/workspace/mindgarden/.cache/storage-clean-checkout/src \
  .venv/bin/python -S .cache/storage-clean-checkout/scripts/mixed_vault_demo.py \
  --workspace .cache/storage-clean-source-proof --recorded-synthetic-pdf \
  --require-source --report .cache/storage-clean-source-proof.json
cmp tests/fixtures/assets/expected-proof.json .cache/storage-clean-source-proof.json
.venv/bin/python -m venv --without-pip .cache/storage-clean-wheel
python3 -m pip --python .cache/storage-clean-wheel/bin/python install \
  --disable-pip-version-check --no-cache-dir --no-index --no-deps \
  --find-links .cache/dist mindgarden==0.1.0
.cache/storage-clean-wheel/bin/python -I \
  .cache/storage-clean-checkout/scripts/mixed_vault_demo.py \
  --workspace .cache/storage-clean-installed-proof --recorded-synthetic-pdf \
  --require-installed --report .cache/storage-clean-installed-proof.json
cmp tests/fixtures/assets/expected-proof.json .cache/storage-clean-installed-proof.json
.cache/storage-clean-wheel/bin/python -I \
  .cache/storage-clean-checkout/scripts/document_demo.py \
  --workspace .cache/storage-installed-pdf-proof --tool-directory /usr/bin \
  --require-installed --report .cache/storage-installed-pdf-proof.json
.cache/storage-clean-wheel/bin/mindgarden validate --repository-root tests/fixtures/public-garden
.cache/storage-clean-wheel/bin/mindgarden verify --repository-root tests/fixtures/public-garden
.cache/storage-clean-wheel/bin/mindgarden publish verify --repository-root tests/fixtures/public-garden
```

V0 results: three notes validate; three notes/one context pack verify; deterministic
public projection verifies two notes. No Google or model service is involved.
The recorded reader is explicitly a synthetic port. The actual installed PDF
proof records Poppler 25.03.0. Neither proves confidential host isolation.

### Automatic CI, separately observed

| Draft / exact observed head | Automatic Test run | Status |
| --- | --- | --- |
| #80 / `15cf5713a318225bb3977cf4ff38e2e1f6a59899` | [42201877954](https://github.com/egohygiene/mindgarden/actions/runs/42201877954) | Passed |
| #81 / `603f82620c5e3eaf07e768901e5fe4ea74b77d9c` | [42203405026](https://github.com/egohygiene/mindgarden/actions/runs/42203405026) | Passed |
| #82 / `55eedd25f66838482c015ffaabff676d3fd166dd` | [42205123720](https://github.com/egohygiene/mindgarden/actions/runs/42205123720) | Passed |
| #83 / `f94d0980bf0c429fe0e103d788ad46102bdfe41c` | [42206546302](https://github.com/egohygiene/mindgarden/actions/runs/42206546302) | Passed |
| #84 / `79e39f072c249760e20fd567f679395f37931816` | [42209496631](https://github.com/egohygiene/mindgarden/actions/runs/42209496631) | Passed; both Python/Node matrix jobs succeeded |

Later documentation-head CI is separate; see the live PR for its exact SHA/run.
Local checks are never represented as passing hosted CI. The exact next action
is maintainer review of #74 → #84 in dependency order, with proposed ADR and
external contract disposition kept separate from merging implementation drafts.
