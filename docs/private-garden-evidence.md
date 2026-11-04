# Portable private-garden checkpoint evidence

This finite synthetic checkpoint implements the ten requested work items on an
unmerged draft stack. It does not complete the parent issues or ratify ADR-0007
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

The working-tree proof passes. Final clean-checkout, fresh-distribution and
isolated-wheel observations will replace this pending ledger before declaring
the checkpoint usable.

| Command/check | Current evidence |
| --- | --- |
| `.venv/bin/python -m unittest discover --start-directory tests` | 134 tests passed before the final publication regressions; final suite pending |
| `.venv/bin/python -m compileall -q src scripts tests` | Passed for the working proof |
| `git diff --check` | Passed for the working proof |
| `node --version` | v24.19.0 |
| Pinned Hygiene ADR and Aether continuity schema/headings/limits | Passed at prior checkpoint; repeat at final handoff |
| Fresh sdist/wheel, clean source checkout, isolated installed wheel | Pending final checkpoint |

No new hosted CI pass is claimed. The owner CI matrix includes Python 3.13;
unavailable/unobserved CI is not a passing result. No workflow is manually launched.

## Stack and remaining acceptance

P01–P11 are draft PRs [#52](https://github.com/egohygiene/mindgarden/pull/52)
through [#62](https://github.com/egohygiene/mindgarden/pull/62), each based on its
predecessor. P12a is [#63](https://github.com/egohygiene/mindgarden/pull/63), with
functional commit `16394c4` and handoff `afbd420`. P12b is the combined
`milestone/13-offline-workflow-proof` checkout based on P12a. CONTINUITY.md records
its draft PR and verified functional revision after creation.

Final review corrected empty publication allowlists to deny values, as the
existing v1 contract requires. Routing, validation and public query selection
share the rule. Private request/catalog hashes and routing labels stay in private
audit records; public lineage represents the reviewed public selection. Required
target read/write contracts are checked explicitly.

| Item | Completed checkpoint | Remaining parent scope | PRs | Verification | Next action |
| --- | --- | --- | --- | --- | --- |
| #42 | Ownership map and four proposed ADRs | Human ratification, broader architecture | #52 | Pinned decision checks | Review ADR-0007–0010 |
| #10 | General v1 integrity/publication, v0 compatibility | Wider consumer/publication conformance | #53, #54, P12 | Schema, hash, path, migration negatives | Review validation/compatibility |
| #11 | Text adapter, exact identities, digest-bound plans, extension | Mindcap/bookmark and other adapters | #57 | Duplicate/stale/extension fixtures | Review adapter boundary |
| #12 | Knowledge/claim search, graph/backlinks, exact evidence, context | Federation, consumer/scale acceptance | #58, P12 | Retrieval, budgets and rebuilds | Review finite usability evidence |
| #13 | Six authored dispositions, evidence, separate human review | Optional models, broader asset curation | #59 | Authority, stale/conflict fixtures | Review authored plan contract |
| #15 | Both versions/profiles of v3.2.2/v3.2.3 | Historical specs, collections/multipart, full producer conformance | #60 | Four profile/version cases, overlap/hostile packages | Obtain exact missing contracts |
| #14 | Explained private fallback, one home, references, recovery | Existing moves/splits/transfers, full registry/organization integration | #61, P12 | Garden kinds, public review/denial, rollback | Review routing and transfer boundary |
| #29 | Independent scope axes and inherited restrictions | Normative Hygiene policy/assurance | #55, #62 | Public/personal/org/restricted/mixed fixtures | Obtain versioned owner contracts |
| #31 | Authorization before bodies/ranking, safe metadata/caches, revocation | Realm/provider/encryption assurance | #62, P12 | Adversarial no-model retrieval | Review local reference boundary |
| #45 | Bounded filesystem audit/export/restore/relocation | Asset/triage/retention, #30/#35, encryption/providers/platform proof | #56, #63, P12b | Corruption, missing, stale, recovery, offline proof | Review local checkpoint; retain full #45 scope |

This supports [#20](https://github.com/egohygiene/mindgarden/issues/20), without
proving a real legacy archive, optional AI producer, Empathy package consumption,
`/garden` publication, public federation or final consumer acceptance. Real private
archives and unavailable historical specifications were not replaced with invented
support. SQLite #32, federation and the broader application remain later work
after their required contracts are ready.
