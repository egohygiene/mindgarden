# Synthetic authored compaction fixture

`seed-curation.json` supplies explicit synthetic human review for two message
evidence anchors from the existing v3.2.3 conversation archive fixture.
`authored-plan.json` declares 13 derived nodes across all six layers and all seven
actions. `retention-policy.json` matches its inline preserve-first policy.
`curation.json` supplies the separately authored, reviewed compacted prompt with
exact citations, uncertainty, unresolved alternative-branch annotation and an
explicit supersedes reference. Originals and the earlier knowledge remain.

No model generated these plans. The alternate-branch conflict annotation is an
authored fixture choice, not an automated contradiction finding. Statement/evidence
coverage and byte ratios are measurable; semantic truth remains a review concern.
`expected-proof.json` records the reproducible local result. Test fixtures exercise
changed evidence, selective invalidation, qualification loss, unsupported policy,
forbidden deletion, public downgrade, budgets and preserved unreviewed authority.
No real archive, credential, private Garden or external service is needed.

`source-only-plan.json` and the synthetic `source-grants.json` wrapper prove the
first segment/summary without creating any knowledge anchor. The grants are test
data, not portable authority or a real session. `tests.test_source_compaction`
captures the same archive and tests source grants, unchanged unreviewed state,
private bundle create/repeat/check, corruption, expiry/revocation, changed inputs,
and partial-output recovery without changing originals. Software fixtures do not
establish semantic summary accuracy or an approved real private pilot.
