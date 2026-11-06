# Merged source pipeline and private-storage checkpoints

The maintainer authorized merging the complete stack. PRs #74–#84 were marked
ready, retargeted to main after their prerequisite merged, and merged in ascending
dependency order on 2026-11-06. Each merge used its verified expected head SHA and
preserved commit ancestry. No branch was deleted, no parent issue was closed and
no ADR was ratified. All 38 parent issues remain open.

## Exact merge receipts

| PR | Approved/tested head | Merge commit | Pre-merge automatic Test |
| --- | --- | --- | --- |
| [#74](https://github.com/egohygiene/mindgarden/pull/74) | `33fe7cf35f82ba0e93e3e707540498cded689abd` | `9b767617bedd6fbb23134ee641d2aad47604ff10` | [42172135507](https://github.com/egohygiene/mindgarden/actions/runs/42172135507) passed |
| [#75](https://github.com/egohygiene/mindgarden/pull/75) | `046a8ad9fa9e1295404bed61fe1eac1fc2cdb0d2` | `f364d83593d6838c6f137c53fb07ddd5df78aa17` | [42172295516](https://github.com/egohygiene/mindgarden/actions/runs/42172295516) passed |
| [#76](https://github.com/egohygiene/mindgarden/pull/76) | `3fe5689eca924387e4a7138dea3221f36d5603a9` | `1bf4e6e4557cf819679179901c92eb630e75bd2e` | [42176087142](https://github.com/egohygiene/mindgarden/actions/runs/42176087142) passed |
| [#77](https://github.com/egohygiene/mindgarden/pull/77) | `a6aa934f88b13dcca93fac404c79887e16ed1b1b` | `6d5bd2947757ea5246dc0df43e97f8c1689b63ea` | [42176123517](https://github.com/egohygiene/mindgarden/actions/runs/42176123517) passed |
| [#78](https://github.com/egohygiene/mindgarden/pull/78) | `fef556e856dc51a8697bc1bc76c4e2b65981de7f` | `1b3c5185e8d247b68244d3e2cc023a7667aa01fc` | [42176128594](https://github.com/egohygiene/mindgarden/actions/runs/42176128594) passed |
| [#79](https://github.com/egohygiene/mindgarden/pull/79) | `8e15314cb3419b1defaf1866aa6450d6703abb09` | `148afad874337d60c2acfbd047c5090c1b77e5af` | [42177086645](https://github.com/egohygiene/mindgarden/actions/runs/42177086645) passed |
| [#80](https://github.com/egohygiene/mindgarden/pull/80) | `15cf5713a318225bb3977cf4ff38e2e1f6a59899` | `56ea42d8b950a02e04139a93d4b47ccac93c2120` | [42201877954](https://github.com/egohygiene/mindgarden/actions/runs/42201877954) passed |
| [#81](https://github.com/egohygiene/mindgarden/pull/81) | `603f82620c5e3eaf07e768901e5fe4ea74b77d9c` | `10b0272c37334ebd9522afa120e2a08ba4a1b0a0` | [42203405026](https://github.com/egohygiene/mindgarden/actions/runs/42203405026) passed |
| [#82](https://github.com/egohygiene/mindgarden/pull/82) | `55eedd25f66838482c015ffaabff676d3fd166dd` | `8f24deac1eaf5faff900b8abdd17bdb89957a1a9` | [42205123720](https://github.com/egohygiene/mindgarden/actions/runs/42205123720) passed |
| [#83](https://github.com/egohygiene/mindgarden/pull/83) | `f94d0980bf0c429fe0e103d788ad46102bdfe41c` | `a65db1d8b03609446253be22cbd4aa788c8cc4f0` | [42206546302](https://github.com/egohygiene/mindgarden/actions/runs/42206546302) passed |
| [#84](https://github.com/egohygiene/mindgarden/pull/84) | `44635f2d7901ab5d7674b9f6759934afcb21e651` | `eb0018e3312f85f7b00818cb483ef4bce1863233` | [42210390897](https://github.com/egohygiene/mindgarden/actions/runs/42210390897) passed |

The initial main was `30a29668a02740a91e77aec22f670a8270ccddf4`. The final merged stack is
`eb0018e3312f85f7b00818cb483ef4bce1863233`, whose complete tracked tree is identical to the tested combined leaf
`44635f2d7901ab5d7674b9f6759934afcb21e651`. Both have tree `6b44305d0973333d66528a408f0445211642be4b`. Every approved PR head remains an ancestor.
A later documentation-only receipt commit may advance main without changing this
functional baseline.

## Verification

- Every PR's exact head had successful hosted Python 3.12/3.13 + Node 24 CI before merge, including #84's final documentation head.
- The combined local suite passed **298 tests with no skips on each Python 3.12.14 and 3.13.5**; exact commands/results remain in [the storage sprint](private-storage-sprint.md).
- `git diff --exit-code 44635f2d7901ab5d7674b9f6759934afcb21e651 eb0018e3312f85f7b00818cb483ef4bce1863233` passed: the complete merged tree is the tested tree.
- `git merge-base --is-ancestor HEAD_SHA eb0018e3312f85f7b00818cb483ef4bce1863233` passed separately for every exact approved head in the table.
- `.venv/bin/python scripts/mixed_vault_demo.py --workspace .cache/merged-74-84-proof --recorded-synthetic-pdf --require-source --report .cache/merged-74-84-proof.json` passed after merging on main.
- `cmp tests/fixtures/assets/expected-proof.json .cache/merged-74-84-proof.json` passed: four assets, twelve objects, exact archive/PDF citations and a bounded 4,486-byte context survive retained-original triage, interrupted rebind, restore/relocation and clean projection rebuild.

The recorded PDF reader is explicitly a synthetic port. Separate real Poppler
25.03.0 source/installed-wheel proofs, clean source/wheel golden equality, v0
smoke checks and zero runtime dependencies are recorded in the storage sprint.
There are no model/Google requirements or real private fixtures. No paid workflow
was manually launched. Hosted CI on subsequent main/documentation commits is
separate from the exact pre-merge head runs above.

## Remaining scope and next action

The source-workflow and private-storage checkpoints are merged implementation,
with bounded synthetic evidence. Parent consumer/publication criteria, accepted
Hygiene/Realm policy and confidential runtime, native macOS/Windows mutation,
provider/encrypted/power-loss proofs, approved-copy policy and timed/destructive
retention remain open. ADR-0007–0024 remain proposed with null approval.

Await the maintainer's next issue group; refresh live state and dependencies
against this merged baseline before implementation. Do not repeat the completed
stack or treat merge authorization as architecture-policy acceptance.
