# Local scoped retrieval reference checkpoint

Search, typed graph traversal, backlinks, context and agent entrypoints share
`QueryContext`, the local draft scope policy and the same authorization view.
No model or service decides access. This is the deterministic local portion of
#31; the required normative Hygiene #39/#40 and released Realm assurance/provider
inputs remain explicit integration gaps. Realm #25 is an available program tracker,
with current remaining acceptance owned by Realm #60; its confidential runtime
outcome is not proved by this repository. The implementation makes no organization-policy,
authentication, encryption or process/network isolation claim.

## Authorization before content

Only explicitly readable, permitted garden bindings are inspected. Denied garden
roots and unrelated vault bindings are not opened or probed. Within each selected
garden, the service reads authorization metadata before any body. Unknown policy,
conflicting classification, unidentifiable/malformed metadata and ambiguous typed
identity are denials, not data-bearing diagnostics. Complete owner validation
remains available independently; a scoped query is not a full garden audit.

Binding policy, execution and available persistence capabilities are checked
before probing a physical garden root, including when a visibility is explicitly
listed. The scope-authoring tool uses the same selector. Explicit scope arguments
take precedence over CLI/library version dispatch and cannot fall back to unscoped
v0 results or cached input. V0 owner operations without scope arguments retain
their existing compatibility behavior.

The metadata pass removes dependencies on unavailable/denied evidence and
propagates scope through source inputs, claims, endpoints and provenance, including
cycles between an artifact and its provenance. Incompatible mixed derivations
are denied before body reads. Only the selected, permitted evidence closure is
opened for checksum and exact-selector verification. Source review is not silently
promoted: unreviewed capture can support an explicitly reviewed citation, but raw
sources never become ranked knowledge. Knowledge review states come from the
explicit session, with approved active records the ordinary retrieval default.

The candidate budget is applied after authorization and sensitivity inheritance.
It selects a stable identity-ordered window, before lexical scoring or traversal.
Result count, graph depth, whole-item context count and serialized UTF-8 byte
budgets apply afterward. Explicit denied/absent includes and traversal targets
are indistinguishable and never enter an exclusion ledger. A stale explicit
include revision is excluded with a reason. Claims and backlinks retain review,
effective sensitivity and exact represented sources.

## Revisions, metadata and failure

Session readable revisions hash the authorized metadata/evidence closure,
effective scopes and relevant manifest contracts/policy. They omit denied records,
unreferenced sources, hidden relationships and generated state. Hidden claims,
synapses, contradictions and supersession links are pruned from the representation.
Changing denied bodies, paths or unrelated bindings therefore cannot change a
visible count, input revision or result. Earlier draft whole-garden query pins must
be refreshed with `mindgarden scope`; owner write-plan pins remain unchanged.

Expiry, revocation, session mutation, relevant binding changes and authorized view
changes are checked before work and again before returning or selecting generated
output. Locked/interrupted writes stop reads. Authorized corruption produces a
generic `QUERY_INTEGRITY` diagnostic with no body, source name, physical path or
partial stdout. Detailed local owner validation is a separate authorized operation.
Denied identifiers never appear in counts, ranking reasons, backlinks, snippets,
traversal results, selection ledgers or shareable diagnostics.

## Derived outputs and caches

Request/query scope joins the contributing restrictions; omission means personal.
Personal and organization contributors yield restricted output requirements, not
an invented visibility ordering. Publication authority is a ceiling. Retrieval
cannot declassify data or grant publication review. The separate reviewed routing
operation handles the bounded public-placement contract.

Generated files live under private owned scope directories, keyed by the complete
explicit session. Directories use 0700 and created files 0600. A session cannot
select a less restrictive destination than the derived output, and unsupported
restricted persistence is refused. Public caches cannot receive private or mixed
results. Retrieval always rebuilds from authorized canonical inputs; stale cached
bytes are never authority. `--check` compares only the current scope directory.
Old private scope files may remain for the owner; revoked sessions cannot read or
write through the application. This does not claim to revoke an owner's direct
filesystem access or previously exported bytes.

The committed adversaries in `tests/fixtures/scoped-retrieval/cases.json` and
`tests/test_scoped_retrieval.py` cover denied bodies and metadata, dependency
inheritance, hidden backlinks, explicit includes, cache poisoning/isolation,
budgets, expiry, mid-query revocation, unknown policy, corruption and partial
write locks. All evidence is synthetic. No paid or model workflow is required.
