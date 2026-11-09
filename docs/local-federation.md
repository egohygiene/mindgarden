# Private local discovery and progressive reads

Refs #16, #12, #29 and #31. This additive local application surface reuses existing
garden IDs, manifests, scopes, represented revisions and sessions. It introduces
no alternative garden ownership or session authority model. The public federation
protocol remains separate and unchanged; private metadata is never inserted into
its descriptors/catalogs. Google, GitHub hosting, a model and a database are optional.

## Discover before opening bodies

```sh
mindgarden federation local-discover --local-config /private/bindings.json \
  --scope /private/session.json
```

The explicit session must permit `index`, be offline, have a personal or
organization request scope and a never-exportable publication ceiling. Discovery
verifies authorized metadata and exact represented revisions before returning a
`mindgarden.local-federation-catalog/v1`. It includes logical IDs/URIs, kind/title,
authorized approved active record counts, scope, versioned contract names and
permitted read operations. No bodies, snippets, provider credentials, physical
locations or source text enter this private control projection. It is metadata,
not a generated whole-garden summary or a claim that all body bytes are healthy.

`body_verification: not-performed` is deliberate. A corrupted body does not become
verified because discovery succeeded. Selected retrieval performs ordinary full
authorization/evidence/integrity checks. Denied/unreviewed records do not contribute
to catalog counts. Discovery uses session candidate/result/byte limits and an
explicit `--max-gardens` ceiling (at most sixteen). No count over denied gardens is
published. The catalog records its own digest, live authority and expiration.

`--garden-id GARDEN` may repeat to narrow already authorized bindings before root
probing. An unavailable unselected peer need not block healthy selected work.
Unknown/denied selections fail generically. Selecting an unavailable or corrupt
required input fails closed; no old catalog records are silently reused. Linked
gardens may need selection together because the original exact session revisions
include their authorized dependencies. The engine never broadens the selection
or invents replacement revision pins to avoid that error.

## Select an existing read handler

A `mindgarden.local-federation-query/v1` request selects exact garden/revision
pairs from the live session. Its closed variants permit only `search`, `graph`,
`backlinks`, `outbound`, or bounded JSON/Markdown `context`. Each variant defines
its parameters; unknown operations or extra execution/authority fields fail.

```json
{
  "schema": "mindgarden.local-federation-query/v1",
  "gardens": [{"garden": "example-garden", "revision": "sha256:REPLACE_WITH_EXACT_VIEW"}],
  "operation": "search",
  "query": "exact evidence",
  "limit": 10
}
```

```sh
mindgarden federation local-query --local-config /private/bindings.json \
  --scope /private/session.json --input /private/selected-query.json
```

The selected application services filter before ranking/traversal and keep exact
provenance, review, budgets and sensitivity. Context profiles use the existing
contract. Input metadata pins are checked before body access. Source instructions
and requested operation names cannot become executable code, new tools or new
permissions. A future CLI/API/web/agent caller can invoke `discover_local` and
`query_local`; the same existing session remains authoritative throughout.

## Private persistence and recovery

Discovery is read-only by default. `--output-directory /private/catalog-01`
previews a private create-or-verify bundle. Inspect the digest, then repeat with
`--apply --plan-digest SHA256`; `--check` revalidates the same live inputs. Mode
0700/0600 ownership, exact membership and checksums apply through the shared
generated-output adapter. Output cannot overlap canonical records or vaults.
Conflicts or partial outputs are preserved for inspection, never auto-repaired.

Caches and catalog files grant no query capability. Expiration/revocation blocks
application checks and reads; it does not erase an owner's previously exported
bytes or revoke direct filesystem access. A fresh session must explicitly pin its
current authorized views. No network refresh or remote authentication is claimed.

Ordinary local organization metadata is tested under the **draft local policy**.
Combining organization and personal contributions requires restricted processing;
this filesystem checkpoint refuses it because confidential runtime/storage is
unavailable. It does not claim ratified organization assurance or declassification.

## Ownership and remaining gates

Aether main `5077797448d32a59b06eabe4b38f091137d58052` and Akashic main
`caeaf6bbe519701110ffda3888d2ee49898c52ec` were refreshed. Aether #69 and Akashic
#176 remain open; no matching accepted session/garden integration contract or
producer fixture is available at those inspected owners. The application uses
Mindgarden's supported local session contract and makes no Aether compatibility
or Akashic producer acceptance claim. Missing external contracts are not invented.

The public descriptor's unavailable private-federation capability refers to that
public remote protocol. This local-only surface does not advertise private
identities publicly or change its wire. Remote acquisition/query/write, signing,
package installation, automatic AI summaries, provider identity and real consumer
proof remain unavailable/deferred. ADR-0011 is extended as a proposal only.
