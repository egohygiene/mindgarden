# Archive adapter 1.1.0 golden reconciliation

The #15 adapter declares version 1.1.0 for attachment selection and opaque JSON
attachment handling. A newly created normalized source records that adapter
version and its ordered transformation. The authorized metadata view therefore
changes even when normalized evidence bytes and their exact references do not.
Existing imported records remain immutable and retain their original attribution.

The first #76–#78 CI runs and the first combined local runs correctly rejected
two stale synthetic golden reports. Earlier demo scripts had completed internal
checks but their output was not explicitly compared to these report fixtures;
those invocations were not proof that the golden comparison passed.

Regeneration on the #15 branch was constrained to these exact changed fields:

- Private workflow: `index_sha256` and `context_sha256`.
- Authored compaction: `context_sha256`.

All source references, selected-text hashes, original ZIP/vault hashes, bodies,
review states, byte budgets and other proof facts remain identical. This is a
versioned metadata-input change, not relaxed integrity checking. Both demo entry
points now compare their complete reports to the committed goldens themselves.
The full tests continue to compare independently.

The two affected proof suites passed 3 tests on each supported Python version.
The correction is propagated from #76 through the dependent drafts using normal
merges. Final combined full-test/CI receipts are recorded in the sprint map;
failed attempts are superseded there, not relabeled as passing.

## Adapter 1.2.0 source-profile expansion

The v2 reader shares unchanged preservation-schema 2.0 checks with v3. The adapter
version and transformation now declare 1.2.0. Regeneration is constrained to the
private workflow's index/context hashes, compaction's context hash and mixed-vault
workflow's index/context/inventory hashes. The inventory carries represented
view revisions and captured provenance metadata; those inputs include the adapter
version. Original content and the vault backup hash remain unchanged. Every other report field must match before a
golden is replaced. This preserves exact original/source hashes, IDs, review,
bodies, budgets and recovery assertions. Focused tests verify the existing v1/v3
profiles as well as v2; no checksum or schema check is relaxed.

The first #114 full CI run (42548628131 at `4c80d08`) failed one Linux
full-suite case: release-journey's embedded copy of the private workflow still
contained the two old index/context metadata hashes. The underlying proof had
already been reconciled. Its nested copy now matches exactly, with a constrained
two-field update. Every other release-journey fact stays identical. The initial
415-case run is recorded as 414 passed/1 failed, not passing CI; native macOS
registry and packaging jobs passed independently. Focused source checks and the
propagated full combined receipts document the correction. No workflow was
manually launched and no release publication occurred.

## Adapter 1.2.1 delivery privacy

Recognized ordinary delivery values remain byte-equivalent, but new imports record
adapter/transform version 1.2.1. Constrained regeneration permits only the private
workflow's index/context hashes, compaction's context hash, mixed-vault's
index/context/inventory hashes and the same nested private-workflow hashes in the
release-journey report. Exact source IDs/bytes/locators, vault hashes, review states,
bodies and budgets remain equal. Existing records are not rewritten. The new
canary fixture is synthetic; its complete metadata remains only in its preserved
private original while portable delivery facts omit runtime details.

The #152 hosted full suite at `6679317` found two additional stale report copies: pipeline completion and the composed reading journey (650 passed / two failed out of 652 on Python 3.12). Their regeneration is constrained to pipeline baseline-proof/index/graph/context hashes and reading-journey index/graph/JSON-context/Markdown-context hashes. All original/vault/source IDs, bytes, exact references, review states, counts, budgets and public subproof fields remain equal. Tests and checksum checks are preserved; the failed hosted run is not relabeled as passing.
