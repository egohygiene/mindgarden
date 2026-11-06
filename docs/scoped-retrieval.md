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

## Output-wide integration checkpoint

The shared `QueryContext` performs a final live-authority check after serializing
query output. Optional session budget `max_output_bytes` bounds serialized index,
search, graph, backlinks, outbound links, context, evidence and agent CLI output;
legacy v1 sessions retain a 16 MiB ceiling. Context/evidence still use their
smaller context ceiling. Internal indexes needed for a small search response do
not consume the response's byte budget. `scope --max-output-bytes` makes a tighter
ceiling explicit without changing existing default session/golden identities.

| Output | Authority and bounds |
| --- | --- |
| Index, lexical search, claims | Shared authorized metadata/evidence closure; review/candidate/result/byte limits |
| Graph, backlinks, outbound links | Same closure before traversal; graph authority for outbound; depth/result/byte limits |
| JSON/Markdown context and `llms.txt` | Same reviewed selection, exact citations, item/context/serialized-byte ceilings |
| Exact evidence and compaction | Authorized reviewed citations, inherited scope, exact spans and context/output bounds |
| Federation/site artifacts and portal composition | Existing explicit reviewed-public selections and manifest pins; independent bundle/site/catalog budgets, no new authority from supplied data |
| Registry/vault/ingestion/review plans | Explicit owner control operations, private local state; never portable publication grants |
| Design/software capability exports | Software configuration only; no garden content or session grant |

Scoped CLI commands accept `--diagnostic-format json`; failures use a closed
reason-code vocabulary and constant remediation, without supplied exception,
parser, path or payload strings. They emit no partial stdout. V0 owner commands
without scope/binding arguments retain their compatibility behavior.

Each newly written scoped cache has `scope-cache/v1` ownership metadata binding
its garden/session digest, exact member set and checksums. It is private control
state and never query authority. Unknown, corrupt or legacy unmanifested caches
are retained, with a stable refusal; use a fresh session or explicit owner
inspection rather than silently adopting human files. A failed marker commit
leaves an invalid disposable cache, not a valid projection or canonical change.
This inventory enables #30's separate reviewed reversible cache handling.

Synthetic fixtures exercise every query API, agent CLI output, denied metadata,
expiry/revocation, response-budget isolation, sanitized failures and unowned-cache
preservation. Existing public federation/site/portal privacy fixtures continue to
cover their own explicit public-input contracts. Host egress, confidentiality,
ACL and provider certification remain the owning Hygiene/Realm acceptance gap.
