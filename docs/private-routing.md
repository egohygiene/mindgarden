# Authored candidate routing checkpoint

Routing extends the existing curation, garden identity, scope and typed-synapse
contracts. A `mindgarden.garden-catalog/v1` describes explicit logical destinations,
owners, canonical URIs, domains, read/write contracts and scopes. Machine roots
remain in local bindings. Catalog values must match the inspected garden manifests.
This is the safe local portion of #30, not a competing garden registry.

A `mindgarden.routing-plan/v1` embeds an authored curation proposal and exactly one
routing decision per candidate. Decisions supply preferred and relevant garden
IDs, confidence, rationale and nullable public review. Only explicitly approved,
active candidates are placed. The preview binds the entire request, catalog,
bindings, represented evidence and all inspected garden revisions into a digest.
The shared curation application service creates the actual knowledge records.

Exactly one permitted preferred home is selected. Ambiguity, prohibited
destinations or absent preference use the explicitly configured personal fallback.
A missing or incompatible fallback yields `unresolved`, with no implied public
destination. Every preview explains policy decisions and rejected alternatives.
Personal/organization mixtures inherit restricted requirements and remain
unresolved when the available filesystem adapter cannot satisfy them.

Each new unit is identified by `(routing request id, candidate id)` and has one
canonical `{garden, id, revision}`. Additional compatible gardens receive reference
knowledge plus a typed `references` synapse, with no copied original source or
duplicated canonical body. Reruns verify identical records. A changed already
placed request fails with `ROUTE_REVISION_REQUIRED`; an inconsistent second home
fails with `ROUTE_TRANSFER_REQUIRED`. Renaming, moving existing knowledge,
splitting/merging already placed units and automated supersession require an
explicit transfer/revision contract. The private lifecycle and reference-repair
contracts below now implement those reviewed operations; public/policy-changing
transfers remain parent scope. Curation's authored merge and explicit
supersession remain available independently.

Deferred/excluded candidates create no placed knowledge. Their exact selectors
and authored reasons are retained through the existing curation service in the
embedded proposal's explicitly catalogued personal controller. The routing
receipt retains the `history-only` decision and inherits its scope. A missing,
public or organization controller fails with `ROUTE_HISTORY_PRIVATE`, rather than
dropping the history or sending it to a preferred public destination. Receipts
participate in the same reviewed digest, capability validation, stale-input
checks, non-overwriting group cutover and rollback as kept outputs. See the
[acceptance audit and synthetic disposition cases](curation-routing-design-acceptance.md).

Public placement additionally requires explicit human public review, approved
normalized public evidence, approved knowledge review and the target publication
allowlist. Private sources never become public by applying or routing a proposal.
Empty allowlists grant no values; a fresh public garden therefore denies routes
until its kind/domain/topic allowlists are explicitly reviewed and configured.
Raw captures remain excluded. General staged validation rechecks all public and
cross-record invariants. Private rejected alternatives remain in the private
preview. Public placements require an explicit personal controller for private
request/catalog hashes and routing labels. Public provenance and curation receipts
represent only the selected reviewed public proposal; raw private plan digests and
labels are not copied into public records. Other per-home receipts omit rejected
alternatives and incompatible destination refs.
Review the entire public placement, including its attribution and identifiers.

```sh
mindgarden route --local-config /private/bindings.json \
  --catalog /private/catalog.json --input /private/routes.json --plan
mindgarden route --local-config /private/bindings.json \
  --catalog /private/catalog.json --input /private/routes.json --explain
mindgarden route --local-config /private/bindings.json \
  --catalog /private/catalog.json --input /private/routes.json --apply \
  --plan-digest REVIEWED_SHA256
mindgarden route --local-config /private/bindings.json \
  --catalog /private/catalog.json --input /private/routes.json --check
```

`--check` returns contract exit 3 for unresolved candidates. Plan/explain/check are
read-only. Authored input files and previews can contain private metadata and stay
outside public repositories.

## Failure and recovery

The local checkpoint is single-writer. Apply locks all targets in stable identity
order, stages and validates the combined result, and persists a private operation
journal beside the local bindings before selecting any tree. Ordinary validation
and combined reads refuse a locked state. A selection failure restores all
originals. A failed rollback retains the journal, locks and last original backups.
There is no claim of a distributed filesystem transaction or multi-writer isolation.

```sh
mindgarden route --local-config /private/bindings.json --recover \
  --plan-digest INTERRUPTED_SHA256
```

Recovery verifies every explicit binding, lock, temporary path and before/after
checksum before modifying any tree. An uncommitted journal rolls back; a committed
journal finalizes cleanup. Repeating interrupted cleanup converges. An unexpected
human change or corrupted last original stops recovery with evidence retained;
restore the verified original rather than deleting the journal or backup. Recovery
also loads bindings when a locked garden is temporarily between tree selections.

`tests/test_routing.py` builds synthetic repository, organization, personal and
public gardens and exercises explained fallback, no fallback, stable references,
public review, reruns, conflict refusal, partial selection failure and failed
rollback followed by CLI recovery. Full #14 and #30 integration remains open.

## Private move and merge checkpoint

`mindgarden route --local-config BINDINGS --transition REQUEST --plan` previews
`mindgarden.routing-transition/v1`. Apply with `--apply --plan-digest SHA256`;
`route --recover --plan-digest SHA256` uses the existing multi-garden journal.
A request names exact `from` revisions, `to`, operation (`move` or `merge`),
creation time, rationale and a separate human authority/approved review.

A move creates a reviewed derivative with the same body, source evidence,
authors, classifications, aliases, tags and qualifications. It preserves the
original record and bytes. The later transfer checkpoint copies up to 128 exact
outgoing claims/synapses, retaining their original review, authors, evidence,
confidence and qualifications. Unreviewed attached claims remain unreviewed;
external targets and incoming relationships are not silently rewritten.
A merge first needs an existing reviewed authored merge with exact lineage to
every input, then records retirement of those inputs. No source is deleted.

Append-only `x-routing-transition` events use existing provenance records, with
versioned event validation. `canonical_reference` follows the reviewed alias
chain; the caller must separately authorize target access. Retrieval excludes
retired homes and their claims before ranking, even if only the old garden is
selected. Original bodies may still be read as authorized provenance of a new
derivative. Transition metadata participates in session revisions, expiration
and revocation checks; it never grants additional access.

This bounded implementation requires matching ordinary personal policies. Public
moves, policy-changing transfers, incoming graph retargeting and wider filesystem/
power-loss behavior remain parent scope. A missing permitted target is an error,
never an implicit public destination. Tests preserve every old file, prove one
searchable home, exact aliases and authored merge lineage, reject stale authority,
and recover both gardens after a simulated second cutover failure. New plan/event
semantics remain a proposed decision, separate from implementation evidence.

## Reviewed split and replacement proposals

`mindgarden.routing-transition/v2` and its explicit v2 event add `split` and
`supersede`; the v1 schemas remain unchanged. Both operations require one exact
reviewed original. A replacement must already be authored and approved, carry
exact original lineage, and explicitly list the original in `supersedes`.

For a split, first curate two to sixteen distinct reviewed children, each deriving
from the exact original. Then curate one reviewed map/reference anchor with exact
approved links to those child revisions and original lineage. The request's `to`
names that anchor; `split_targets` names every child. Only after validation does
an append-only event retire the original. Old references resolve to the anchor,
which explains the new units. A split does not give one unit several canonical
homes and does not automatically segment source text or approve proposals.

All original bytes, evidence and identities stay available. Exact graph metadata
copies record their original reference and request digest. Copies keep graph
review unchanged rather than approving attachments during a move. Conflicting
output files, stale endpoints, mismatched policy and unreviewed/missing split
lineage fail before cutover. Existing multi-garden staging/journaling rolls back
both gardens if a simulated second cutover fails; retry is idempotent.

These are bounded implementation proofs under proposed ADR-0022. General incoming
edge migration, alias/entity reconciliation, declassification, public/organization
policy transitions and wider platform/power-loss recovery remain parent scope.
No owner or ADR approval is inferred from tests or a merged implementation.


## Incoming-reference review inventory

A move/merge/split/replacement plan now inventories up to 128 active, independently
approved incoming synapses under the same ordinary personal policy. It includes
the exact edge reference and revision, original source/target, relation direction,
review and proposed current canonical target. Unreviewed/inactive edges, stricter
policies, unreviewed sources and retired source homes are omitted without counts.
This inventory is a private plan aid, not a complete cross-scope graph census.

Each entry says `separate-reviewed-reference-repair-required`. A historical
`supports` or `contradicts` relation may concern the old statement specifically;
a canonical-home move is not authority to rewrite its meaning. Existing edges and
their owners stay byte-identical after application. Unpinned and undirected forms
remain explicit rather than being silently upgraded to exact directed claims.
The current target hint does not authorize retrieval, graph access or public
publication. Exact input checks bind the inventory to the reviewed transition.

Six new cases prove deterministic exact inventory, unchanged original links,
unreviewed/stricter omissions, stale-edge refusal before cutover, unpinned and
undirected preservation, and the 128-entry bound. The existing move/split/merge/
replacement/transaction suites retain rollback, retry and one-home proofs.
The separately reviewed repair operation below supplies exact replacements;
public/policy-changing transitions remain open.
This is a bounded #14 checkpoint under proposed ADR-0022, not ratification or a
claim of complete incoming migration.

## Reviewed incoming-reference repair

The journey checkpoint adds `route --reference-repair FILE` over versioned request/event contracts. It requires exact pinned edge, source, historical target and current reviewed canonical successor, a fresh replacement identity, rationale and explicit human approval. Matching ordinary personal policies are required for every contribution. The existing edge and source owner are retained byte for byte; the new edge keeps type, direction, attribution and evidence. Its logical review pointer and the event's exact represented replacement avoid a recursive hash while binding the entire authorized closure.

The repair event also pins every canonical-transition provenance record on the selected path. This keeps validation/rebuild possible without opening other garden bodies. Old historical-target edges are absent from current induced graphs because their knowledge target is retired; no read silently changes their intent. A later target move preserves the historical repair but requires another explicit review of its current replacement. Conflicting repairs and unpinned historical endpoints are refused.

The existing group journal governs multi-owner rollback/retry; originals and vault bytes are never rewritten. See [exact commands, tests and remaining scope](journey-sprint.md). Proposed ADR-0022 is unchanged in status and approval.
