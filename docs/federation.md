# Public federation projection checkpoint

The additive #16 checkpoint builds supplied local v1 records into checksum-bound
public discovery artifacts. It uses the existing Python application services and
CLI. Google, GitHub hosting, model providers, web servers and databases are not
required. [ADR-0011](decisions/ADR-0011-public-federation-projections.md) is proposed;
this implementation does not ratify it or complete the broader federation issue.

## Inputs and authority

Supply explicit machine-local bindings and a `mindgarden.session/v1` session
whose allowed visibility is exactly `public`, review state exactly `approved`,
requested scope public, and publication authority `publishable`. The session must
permit `index`, `graph` and `llms`. Normal expiration, revocation, represented
revision and output-budget checks apply. Applying an export also requires the
target garden to be the session's explicit writable garden.

Use the existing `mindgarden.projection/v1` profile with kind `federation`, status
`planned`, public visibility and explicit human approval. `source_revision` pins
the current **authorized public view** from the index's `inputs`; this checkpoint
supports its `sha256:` form. `inputs` selects exact immutable knowledge/claim
references, including each claim's reviewed subject. Empty inputs mean an empty
projection. Garden and profile allowlists both apply. Empty kind/domain/topic
allowlists never grant publication for values absent from them.

Public visibility is separate from publication authority. Review-required and
never-exportable records and evidence closures are removed before bodies are
opened and before public revisions/counts are computed. Unknown scopes/policies
fail closed. Applying a proposal never manufactures review or factual authority.

`base_uri` is a credential-free canonical HTTPS base ending in `/`. Local literal
hosts/IPs, query strings, fragments, traversal, symlinks and ambiguous paths are
rejected. This validates declared routes; it does not perform DNS, HTTP, hosting
or network-isolation verification. V1 note routes are declared as
`<base_uri>notes/<id>/`; serving them is retained #17 acceptance. V0 routes remain
unchanged. Exact citations use logical source IDs/revisions/selectors, independent
of absolute source storage locations; HTTP source-serving is not implemented.

## Plan, apply and check

Create the export parent explicitly. The profile's portable `output_root` selects
the immutable bundle directory beneath `--output-directory`; parents must exist.
The example profile uses `federation`. Export targets cannot overlap canonical
`.garden` records or declared private vaults.

```sh
mindgarden federation build \
  --local-config "/private/bindings.json" \
  --scope "/private/public-session.json" \
  --profile "/private/reviewed-federation-profile.json" \
  --output-directory "/private/exports/revision-a" \
  --plan
```

Inspect the plan, then repeat with `--apply --plan-digest "<plan_sha256>"`.
Use `--check` to verify the existing bundle against current reviewed inputs.
Changed profile bytes, authority, destination or represented inputs invalidate
the plan. Plans are private control documents; do not publish their digests as
public lineage. Public descriptor revisions bind only the sanitized representation.

The directory contains `garden.json`, `index.json`, `graph.json`, `llms.txt` and
`.mindgarden-federation.json` (ownership marker). All are reproducible. The descriptor
binds the other public artifacts' SHA-256 hashes and byte sizes. The public index
contains selected reviewed knowledge/claims, canonical routes, exact citations,
uncertainty/attribution and inclusion reasons. Graph endpoints must belong to
that selection. Agent instructions identify all linked text as untrusted evidence.
No raw source bytes, local paths, private binding identities, session/profile
hashes or review identities/rationale are exported.

An identical re-apply verifies without changing files. A different, unowned or
incomplete directory is refused; use a fresh export parent and retain the old
one for inspection. The descriptor is written last, and readers verify all
members before using the index. Caught interrupted writes remove only files
created by that attempt where ownership/content can be verified. A crash may
leave an incomplete directory, which remains invalid; automatic repair, concurrent
writers, power-loss durability and destructive cleanup are not claimed.

## Supplied public catalog

The machine-local request uses `mindgarden.federation-catalog-request/v1`:

```json
{
  "schema": "mindgarden.federation-catalog-request/v1",
  "bundles": [
    {
      "directory": "/private/exports/revision-a/federation",
      "expected_revision": "sha256:<exact-public-descriptor-revision>"
    }
  ]
}
```

```sh
mindgarden federation catalog --input "/private/public-catalog-request.json"
```

Only explicitly supplied public bundles are read. The catalog contains canonical
links and selected public metadata, never copied note bodies or machine locations.
Input order does not affect output. Missing, incompatible, stale and corrupt
inputs produce a `partial` catalog with generic stable diagnostic codes while
verified gardens remain usable. Duplicate garden identities or conflicting
canonical homes quarantine all conflicting entries, rather than choosing a winner.
A complete catalog exits `0`; partial coverage exits `3` with the JSON result on
stdout. Other contract failures use existing CLI diagnostics/exit codes.

At most 16 bundles and 10,000 aggregate records are supported. Each serialized
artifact is limited to 2,000,000 bytes and a bundle to 8,000,000 bytes. Session
candidate limits apply before selection; an incomplete selection fails rather
than silently publishing a truncated garden. The agent entrypoint also respects
the session context-byte budget. Large-corpus runtime/memory proof remains #12.

Checksums establish content consistency, not origin authentication, actual human
approval or factual truth. Incoming descriptors remain untrusted producer
assertions. Freshness means agreement with the explicitly selected immutable
revision, not an inferred claim that a remote garden is current or available.

## Reproduce and remaining acceptance

Run the committed synthetic two-garden proof from a new or empty workspace:

```sh
python3 scripts/federation_demo.py --workspace ".cache/federation-demo" \
  --report ".cache/federation-demo-report.json"
python3 -m unittest tests.test_federation
```

The proof compares rebuilt artifacts with committed golden files, verifies
exact source references, relocates the export, rebuilds from a clean synthetic
garden and reproduces the same catalog. Network/process entry points are blocked
in-process and provider environment is cleared; this is not host isolation proof.

The schemas and [coverage ledger](open-issue-coverage.md) retain #16's remaining
private/internal local federation, incremental refresh, signature/authentication,
remote query/serving, rendered route, Akashic/Aether and actual consumer acceptance.
No site is deployed and no parent issue is closed. #30 can consume the supported
identity/version contract, while broader registry/platform/runtime gates remain.
