# Portable private-garden checkpoint evidence

This finite synthetic checkpoint provides bounded results for the ten requested work items.
The original draft stack #52–#64 was merged with maintainer authorization on
2026-11-05 at `9fae752b3cf7eb9c74033a72a12d125c42f8659e`, with exactly the
tested combined tree. [The merge and coverage ledger](open-issue-coverage.md)
records all merge commits and remaining work. It does not complete the parent issues or ratify ADR-0007
through ADR-0010. The Python engine and CLI remain dependency-free with supported
v0 behavior. No release, deployment or consumer publication is claimed.

## Reproduce the local workflow

Use Python 3.12 or 3.13 from a reviewed checkout and a new or empty workspace:

```sh
.venv/bin/python scripts/private_garden_demo.py \
  --workspace ".cache/private-garden-demo" \
  --report ".cache/private-garden-demo-report.json"
```

The script uses the ordinary CLI to initialize privately, initialize a separate
vault, plan/apply a synthetic archive import, repeat without duplicates, inspect
and apply an authored human-review plan, create an explicit session, validate,
search, resolve exact evidence, build bounded context and verify an index. It
exports the vault, relocates it, restores a clean copy, copies the portable garden
to a new location, removes copied projections and rebuilds. Exact references,
context and indexes remain identical.

Committed members under `tests/fixtures/conversation-archives` are synthetic.
`authored-plan.json` explicitly supplies synthetic human review; apply does not
manufacture authority. The assistant suggestion stays epistemically `proposed`
after review, and the source remains `unreviewed`.

Networking and external process entry points are blocked in-process, provider
environment variables are cleared, and no Google/model package is required.
This is no-service operation, not host/network isolation evidence. Separate
routing fixtures prove private fallback, explicit public allowlists, stable homes
and partial-failure recovery across repository, organization and personal gardens.

## Exact portable result

The [committed report](../tests/fixtures/conversation-archives/expected-proof.json)
is checked by `tests/test_private_garden_workflow.py`.

| Evidence | Observed result |
| --- | --- |
| Archive | v3.2.3 full-source, envelope 3.2 / preservation 2.0 |
| Knowledge | `synthetic-garden/reviewed-prompt`, approved, topic `prompt-bank` |
| Source | `source-49101f6a41f4768b98734604-f03c4e39101deeb8` |
| Source revision | `sha256:f03c4e39101deeb851f2138f101805ba2d303706d22e528d376e9137abc22262` |
| Exact selection | `json:/content/0/text`; original `CONVERSATION.json` at `/messages/1` |
| Text SHA-256 | `d427af01c5be2e4de5e41a0cb363c58cd0c1cdd0a0af1577bcfd78f6b8f2d83f` |
| Attribution | Assistant; source remains unreviewed; reviewed knowledge authorizes the citation |
| Context | 2,670 serialized JSON bytes within 16,384; Markdown independently bounded |
| Index SHA-256 | `d3523aba3283c72c05ee76932b353d098d23055dd69076f918d8388bc5c46cdf` |
| Context SHA-256 | `ad4b35cf61e6e89209eb8e5e629e7aac3333a71708614f198426200e2411a2df` |
| Vault backup | Six immutable objects; `c74e215fc9a035abc701ecab54a041ed840e3a6b8201314e151f6834ff0dba5d` |
| Relocation/restore | Identical evidence, context and index; original vault retained |

`mindgarden evidence` accepts the unchanged `source`, `locator` and
`content_sha256` values returned by search. Its flags are `--garden-id`,
`--source-id`, `--revision`, `--locator`, `--content-sha256`, `--local-config` and
`--scope`. It returns bounded text, speaker, original member/pointer, lineage,
effective scope and review authority. Uncited, denied, changed or absent selections
produce the same safe denial.

## Verification ledger

Verified functional revision: `23d2952d705552c91833bbbf015d66bc806df9bc` on Linux.
The clean source checkout and isolated installed wheel reproduce the committed
report byte-for-byte. The finite local workflow is demonstrated; broader parent
and consumer acceptance remains open.

| Command/check | Current evidence |
| --- | --- |
| `.venv/bin/python -m unittest discover --start-directory tests` | 139 passed, no skips; Python 3.12.14 |
| `.cache/python313/bin/python -m unittest discover --start-directory tests` | 139 passed, no skips; Python 3.13.5 |
| Both interpreters: `-m compileall -q src scripts tests` | Passed |
| `git diff --check` | Passed |
| `node --version` | v24.19.0 |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist` | Fresh source/wheel build passed; package/resource assertions passed |
| Clean source checkout with `-S --require-source` | Exact committed report matched; no site packages loaded |
| Isolated wheel with `-I --require-installed` | Exact report matched; only `mindgarden` installed |
| Installed v0 version/help/validate/verify/publish/library smoke | Passed; 3 notes, 1 context profile, 2 public projected notes |
| Pinned Hygiene ADR and Aether continuity schema/headings/limits | Passed; repeated at final handoff |

Exact clean-source and installed-wheel proof commands (from the repository root):

```sh
mkdir .cache/clean-private-checkout-final
git archive --format=tar HEAD | tar --extract --directory .cache/clean-private-checkout-final
PYTHONPATH=.cache/clean-private-checkout-final/src .venv/bin/python -S \
  .cache/clean-private-checkout-final/scripts/private_garden_demo.py --require-source \
  --workspace .cache/private-demo-clean-final --report .cache/private-demo-clean-final-report.json
python3 -m venv --without-pip .cache/private-wheel
python3 -m pip --python .cache/private-wheel/bin/python install --no-cache-dir \
  --disable-pip-version-check --no-index --force-reinstall --find-links .cache/dist mindgarden==0.1.0
.cache/private-wheel/bin/python -I scripts/private_garden_demo.py --require-installed \
  --workspace .cache/private-demo-wheel-final --report .cache/private-demo-wheel-final-report.json
cmp tests/fixtures/conversation-archives/expected-proof.json .cache/private-demo-clean-final-report.json
cmp tests/fixtures/conversation-archives/expected-proof.json .cache/private-demo-wheel-final-report.json
```

`HEAD` was the functional revision above. Later handoff/evidence commits change
documentation only. Python 3.13 dev tools were installed using a workspace venv
without ensurepip and the host pip's `--python` option; they are not runtime dependencies.

Both versions in the owner CI matrix passed locally. Automatic GitHub
[Test run 27](https://github.com/egohygiene/mindgarden/actions/runs/41778548306)
completed successfully on `072ec03229563daff09ce548f683becfca7e6d5d`, whose functional
code is the revision above. Later documentation-only heads may have fresh checks;
the 2026-11-05 merge receipts are in the coverage ledger. No workflow was manually launched.

## Stack and remaining acceptance

At the original pre-merge handoff, P01–P11 were draft PRs [#52](https://github.com/egohygiene/mindgarden/pull/52)
through [#62](https://github.com/egohygiene/mindgarden/pull/62), each based on its
predecessor. P12a is [#63](https://github.com/egohygiene/mindgarden/pull/63), with
functional commit `16394c4` and handoff `afbd420`. P12b is the combined
`milestone/13-offline-workflow-proof` checkout based on P12a, in
[draft #64](https://github.com/egohygiene/mindgarden/pull/64). CONTINUITY.md records
its verified functional revision and complete final handoff. All thirteen PRs were
inspected as open, draft and unmerged; each base is the preceding head:

| Draft | Base branch | Head/combined checkout | Inspected head |
| --- | --- | --- | --- |
| [#52](https://github.com/egohygiene/mindgarden/pull/52) | `main` | `milestone/01-architecture` | `e137ef0` |
| [#53](https://github.com/egohygiene/mindgarden/pull/53) | `milestone/01-architecture` | `milestone/02-v1-validation` | `1f37f56` |
| [#54](https://github.com/egohygiene/mindgarden/pull/54) | `milestone/02-v1-validation` | `milestone/03-provenance-privacy` | `b93969c` |
| [#55](https://github.com/egohygiene/mindgarden/pull/55) | `milestone/03-provenance-privacy` | `milestone/04-scope-bindings` | `dd4be16` |
| [#56](https://github.com/egohygiene/mindgarden/pull/56) | `milestone/04-scope-bindings` | `milestone/05-local-vault` | `febb2b0` |
| [#57](https://github.com/egohygiene/mindgarden/pull/57) | `milestone/05-local-vault` | `milestone/06-source-adapters` | `f655d03` |
| [#58](https://github.com/egohygiene/mindgarden/pull/58) | `milestone/06-source-adapters` | `milestone/07-v1-retrieval` | `8836fdd` |
| [#59](https://github.com/egohygiene/mindgarden/pull/59) | `milestone/07-v1-retrieval` | `milestone/08-curation` | `1a49992` |
| [#60](https://github.com/egohygiene/mindgarden/pull/60) | `milestone/08-curation` | `milestone/09-conversation-archives` | `fb3bcf3` |
| [#61](https://github.com/egohygiene/mindgarden/pull/61) | `milestone/09-conversation-archives` | `milestone/10-private-routing` | `df724c4` |
| [#62](https://github.com/egohygiene/mindgarden/pull/62) | `milestone/10-private-routing` | `milestone/11-scoped-retrieval` | `e31d574` |
| [#63](https://github.com/egohygiene/mindgarden/pull/63) | `milestone/11-scoped-retrieval` | `milestone/12-vault-recovery` | `afbd420` |
| [#64](https://github.com/egohygiene/mindgarden/pull/64) | `milestone/12-vault-recovery` | `milestone/13-offline-workflow-proof` | `ebe11f8` |

The last head receives later documentation-only handoff updates. Functional code
remains pinned to `23d2952d705552c91833bbbf015d66bc806df9bc`.

Final review corrected empty publication allowlists to deny values, as the
existing v1 contract requires. Routing, validation and public query selection
share the rule. Private request/catalog hashes and routing labels stay in private
audit records; public lineage represents the reviewed public selection. Required
target read/write contracts are checked explicitly.

| Item | Completed checkpoint | Remaining parent scope | PRs | Verification | Next action |
| --- | --- | --- | --- | --- | --- |
| #42 | Ownership map and four proposed ADRs | Human ratification, broader architecture | #52 | Pinned decision checks | Review ADR-0007–0010 |
| #10 | General v1 integrity/publication, v0 compatibility | Wider consumer/publication conformance | #53, #54, #63, #64 | Schema, hash, path, migration negatives | Review validation/compatibility |
| #11 | Text adapter, exact identities, digest-bound plans, extension | Mindcap/bookmark and other adapters | #57 | Duplicate/stale/extension fixtures | Review adapter boundary |
| #12 | Knowledge/claim search, graph/backlinks, exact evidence, context | Federation, consumer/scale acceptance | #58, #63, #64 | Retrieval, budgets and rebuilds | Review finite usability evidence |
| #13 | Six authored dispositions, evidence, separate human review | Optional models, broader asset curation | #59 | Authority, stale/conflict fixtures | Review authored plan contract |
| #15 | Both versions/profiles of v3.2.2/v3.2.3 | Historical specs, collections/multipart, full producer conformance | #60 | Four profile/version cases, overlap/hostile packages | Obtain exact missing contracts |
| #14 | Explained private fallback, one home, references, recovery | Existing moves/splits/transfers, full registry/organization integration | #61, #63, #64 | Garden kinds, public review/denial, rollback | Review routing and transfer boundary |
| #29 | Independent scope axes and inherited restrictions | Normative Hygiene policy/assurance | #55, #62 | Public/personal/org/restricted/mixed fixtures | Obtain versioned owner contracts |
| #31 | Authorization before bodies/ranking, safe metadata/caches, revocation | Realm/provider/encryption assurance | #62, #63, #64 | Adversarial no-model retrieval | Review local reference boundary |
| #45 | Bounded filesystem audit/export/restore/relocation | Asset/triage/retention, #30/#35, encryption/providers/platform proof | #56, #63, #64 | Corruption, missing, stale, recovery, offline proof | Review local checkpoint; retain full #45 scope |

The [bounded evidence is linked to #20](https://github.com/egohygiene/mindgarden/issues/20#issuecomment-6623276660), without
proving a real legacy archive, optional AI producer, Empathy package consumption,
`/garden` publication, public federation or final consumer acceptance. Real private
archives and unavailable historical specifications were not replaced with invented
support. SQLite #32, federation and the broader application remain later work
after their required contracts are ready.
