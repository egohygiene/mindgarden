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
