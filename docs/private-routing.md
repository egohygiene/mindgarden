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
explicit transfer/revision contract and remain parent scope. Curation's authored
merge and explicit supersession remain available independently.

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
original record and bytes. Attached claims/relationships/contradictions need an
explicit curation proposal and currently fail with `ROUTE_TRANSITION_COMPLEX`.
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
moves, policy-changing transfers, attached-graph migration and wider filesystem/
power-loss behavior remain parent scope. A missing permitted target is an error,
never an implicit public destination. Tests preserve every old file, prove one
searchable home, exact aliases and authored merge lineage, reject stale authority,
and recover both gardens after a simulated second cutover failure. New plan/event
semantics remain a proposed decision, separate from implementation evidence.
