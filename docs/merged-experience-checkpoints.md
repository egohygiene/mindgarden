# Merged garden-experience checkpoints — 2026-11-06

The maintainer explicitly authorized merging #68–#73. All six were merged in
dependency order after refreshing live heads, comments, review threads and CI.
No submitted reviews, comments or unresolved threads were present. Every exact
head had a successful automatic Test run. Normal merge commits preserve the
original source checkpoints; dependent PRs were retargeted to main in order.

| PR | Merge commit | Original head |
| --- | --- | --- |
| [#68](https://github.com/egohygiene/mindgarden/pull/68) | `a9d240083b7cbf4e2086919e537d863420e69d3a` | `d6d290d0c5d405e469dfccf837ceab9b3d54fbe0` |
| [#69](https://github.com/egohygiene/mindgarden/pull/69) | `50dbe69d1dcde7c4a3e79fe2f4b506da785e0f07` | `85beb8dadd3cdc883156f32d7379b9fe9a5edac7` |
| [#70](https://github.com/egohygiene/mindgarden/pull/70) | `d68e81f8f606d38fa1a18017bbd9c8061b4b2e6d` | `9e134e9c78104fa711208628a2017a27986fe5bf` |
| [#71](https://github.com/egohygiene/mindgarden/pull/71) | `4b833a4e1858b2da87a41ab275fca4e8f9288216` | `2899b298ede1788faf9e426ee4e21708f1b4a9c0` |
| [#72](https://github.com/egohygiene/mindgarden/pull/72) | `a92261e22dcacef67a5dd6c28591096607f5d2e3` | `267e0f18d85b3b760dffc536210ac12b83615cb7` |
| [#73](https://github.com/egohygiene/mindgarden/pull/73) | `30a29668a02740a91e77aec22f670a8270ccddf4` | `eb3eebec474303c8edfe11854382af9d3b3d9e47` |

Main is `30a29668a02740a91e77aec22f670a8270ccddf4`.
Its tree is `93f165223ebb9f0406e4d5501b4da9ea34112923`, exactly
the tested combined checkout `eb3eebec474303c8edfe11854382af9d3b3d9e47`.
Each intermediate merged tree also matched its PR head. The exact comparison was:

```sh
git diff eb3eebec474303c8edfe11854382af9d3b3d9e47 30a29668a02740a91e77aec22f670a8270ccddf4 --exit-code
```

It passed. This reuses the existing 231-test evidence on Python 3.12.14 and
3.13.5, the final 38-test boundary checks on both versions, and clean-source /
installed-wheel site, portal, compaction and private-workflow proofs. No redundant
full local test run is claimed for an unchanged tree. Post-merge main CI is a
separate automatic run, not a manually dispatched workflow.
[Main Test run 42168063685](https://github.com/egohygiene/mindgarden/actions/runs/42168063685)
passed on exact main `30a2966`.

ADRs remain proposed with null approval. Merging implementation/documentation
does not ratify them or satisfy every parent acceptance criterion. All 38 parent
issues remain represented in [the coverage ledger](open-issue-coverage.md).
The earlier [batch map](garden-experience-milestone.md) preserves source/test
checkpoints, renderer/browser evidence and retained acceptance gates.

## Continuation

The maintainer authorized continuing numbered items 7–12. The checked-in roadmap
preserves the completed six (#17/#38/#10/#18/#42/#46) and coverage groups, but does
not preserve the remaining numbered list. The issue IDs were requested from the
maintainer while the merges proceeded. No replacement numbering or implementation
sequence is inferred here. Record the mapping before starting the dependent work.
Preserve Python/v0 and synthetic-only fixtures; leave new work in small draft PRs.
