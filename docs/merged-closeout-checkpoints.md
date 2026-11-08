# Merged closeout checkpoints

The maintainer authorized merging the existing PR stack on 2026-11-08. All
seventeen PRs below merged in dependency order with expected heads checked.
New checkpoint drafts, starting with #110, remain for review.

| PR | Merge commit |
| --- | --- |
| [#93](https://github.com/egohygiene/mindgarden/pull/93) | `92cf997c2c82325999b21ffc821c29ac92d7f6d0` |
| [#94](https://github.com/egohygiene/mindgarden/pull/94) | `86c64c49abb8c920f53f1b40075fa43d3ba7d8ca` |
| [#95](https://github.com/egohygiene/mindgarden/pull/95) | `506e0c68f54f5d5e506ead69046555245b397a0e` |
| [#96](https://github.com/egohygiene/mindgarden/pull/96) | `11bcaa8d59e206b4bd6a2117eff8e80e5580cc7a` |
| [#97](https://github.com/egohygiene/mindgarden/pull/97) | `43aa9d12eeeb8972663fd1941402e24f08798171` |
| [#98](https://github.com/egohygiene/mindgarden/pull/98) | `22a68e6685a58fa214ba50f574570a695743c8d2` |
| [#99](https://github.com/egohygiene/mindgarden/pull/99) | `9c651481d01fe28fdab365ee63b0c17ecec4054d` |
| [#100](https://github.com/egohygiene/mindgarden/pull/100) | `91a6c3b6c9abfa59b5affc9cf77cda49f8663dd0` |
| [#101](https://github.com/egohygiene/mindgarden/pull/101) | `fe3a1dd548a301935540c8263aa2c7da84da14c0` |
| [#102](https://github.com/egohygiene/mindgarden/pull/102) | `a3d27a04e84e4b4c0f4003094f4820c3f56939f4` |
| [#103](https://github.com/egohygiene/mindgarden/pull/103) | `1f2cda5a2b696231baee0ccde5acb2fc70120ac4` |
| [#104](https://github.com/egohygiene/mindgarden/pull/104) | `d8744b91a1889cdd4fa6947a19294f209de85d91` |
| [#105](https://github.com/egohygiene/mindgarden/pull/105) | `9bc4c97700a0e80bd749374caeca214ea26d0a98` |
| [#106](https://github.com/egohygiene/mindgarden/pull/106) | `0c0863bd691e6bf654bfc754542ab3b4576311be` |
| [#107](https://github.com/egohygiene/mindgarden/pull/107) | `a1424caa14c48efdecbebadd846d10beee9a3c09` |
| [#108](https://github.com/egohygiene/mindgarden/pull/108) | `98428eca6febda902eb053d603552a3428d3ea24` |
| [#109](https://github.com/egohygiene/mindgarden/pull/109) | `f3a88ccf7d67deb8ecf188d10d9cd496ed6a4973` |

The final main revision is `f3a88ccf7d67deb8ecf188d10d9cd496ed6a4973`.
Compared with the previously tested combined checkout `fdce5df3b6b96b85865723032360323fafa7035c`,
only ADR-0022/0023/0024 body sections changed. All ADR status/approval metadata
remains proposed/null. The engine, fixtures and tests are unchanged from that
381-test combined baseline on Python 3.12 and 3.13. This is baseline evidence,
not a claim that every subsequent draft has passed the complete suite.

## Native Decisions repair (#43)

Actual owner validation found required body headings missing in those three ADRs.
Repair `7efb049d4d366a875561aa40e4d706457413ae01` supplies the seven canonical
sections without weakening validation or claiming ADR acceptance. The unmodified
Relay collector, prepared with Rust 1.85.1 and the checked-in owner lock, reports
`status: ready` against both the repair and merged main. Publication remains
`denied` pending the separate owner/consumer gates. Unknown roadmap/history
coverage remains explicit.

- Relay: `b4a88db20bc26f9ddefbee174baa8162cbe94ff2`.
- EgoLint: `d917ea524962639494e5bb4b3196192238ba57d9`.
- Hygiene ADR contract: `a05b14f8b9e2772124f879f818e09a911e996ad8`.
- Observatory: `f411b83398dd07aa3d5e6e2c89d1e8dfff746085`.
- Hosted [Decisions preview 42519229741](https://github.com/egohygiene/mindgarden/actions/runs/42519229741)
  succeeded; site artifact `13632886587`, SHA-256
  `2ffcd457d2ae021d8ab7700b02c6838dc0e5fc75e033050d51c0ebea74c34ef1`.
- Hosted Test `42519229319`: all four jobs passed before #97 merged.

Exact local collection command (using an isolated prepared runtime and output
outside the inspected repository):

```sh
python collect_repository_adrs.py collect --runtime "$ADR_RUNTIME" \
  --repository-root "$MINDGARDEN_CHECKOUT" --repository egohygiene/mindgarden \
  --visibility public --source-commit f3a88ccf7d67deb8ecf188d10d9cd496ed6a4973 \
  --observed-at 2026-11-08T20:40:00Z --adoption present \
  --output "$REVIEW_OUTPUT/adr-collection.review.json"
```

This closes the native source defect, not full #43: historical #41, human #42,
shared route acceptance and production publication retain their separate gates.
No release, site publication or deferred #86–#91 work was activated.

