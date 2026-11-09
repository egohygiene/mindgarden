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
