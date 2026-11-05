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
Raw captures remain excluded. General staged validation rechecks all public and
cross-record invariants. Private rejected alternatives remain in the private
preview; portable per-home receipts omit them and incompatible destination refs.
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
