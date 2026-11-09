# Knowledge-pipeline completion sprint

The maintainer selected #11–#16 and their required dependencies. The existing
source-workflow implementation is merged through #74–#79; preserve it. New work
uses small drafts over #112 (`83e553d`) while #110–#112 remain unmerged. That is an
operational review stack, not a claim that TypeSafe or public UI is a prerequisite.
No release, site publication, real private pilot or ADR ratification is authorized.

## Reconciled order and ownership

| Work | Bounded checkpoint | Required dependency / remaining integration |
| --- | --- | --- |
| Mindcap #35 → #11 | Exact producer-owned captured-source wire and bookmark handoff; normalize via the existing plan/apply service | Mindcap draft #42 at `7ee766c`; proposed, not accepted. Full capture deltas/recurrence stay with Mindcap |
| #13 | Optional versioned producer mapping, evidence-bound proposed entities/claims/relations and recoverable authored batches | Existing normalized evidence and curation contracts; no hosted model required. Runtime/model decisions remain proposed |
| #15 | Actual v2 baseline/delivery patch reader and safe independent attachment selection | Reread authoritative v2.0.0/2.0.1/2.0.2 specifications; retain tested v1/v3 profiles. Producer workflow conformance is distinct |
| #14 | Reviewed lifecycle extensions, attached graph preservation and explicit split reconciliation | Existing curation, exact source revisions and recovery transaction. Public declassification/organization assurance needs its owning contract |
| #12 | Typed/cross-garden projection matrix and larger measured corpus | Existing authorized query services, not a special database or whole web application |
| #16 | Machine-local private/internal discovery and progressive scoped retrieval | Existing sessions/sensitivity; no private advertising in public catalogs. Real Aether/Akashic acceptance remains independently gated |

#8 and #9 are closed and their package/v1 contracts exist. #10's local validation
is implemented; its broader normative/runtime assurance does not block synthetic
local checkpoints. The execution order after #11 is the #15 reader, then #13 producer: its
new version fixtures support the extraction proof. #15's dependency on #13 is
satisfied by the existing authored curation contract; it does not require the
new optional producer before deterministic parsing. #14 can use existing #12 retrieval before the later performance proof.
#16 local discovery can proceed without remote acquisition, package installation,
signatures or a public hosting service. Missing external contracts are recorded;
they are not replaced by claims of compatible support.

## Current checkpoint

Mindcap's current main is `ce5f709`; it has no provider-neutral handoff. The new
[Mindcap #42](https://github.com/egohygiene/mindcap/pull/42) proposes a schema,
deterministic byte package and explicit existing-bookmark exporter. Full owner
suite: 622 tests pass (4.82s); repository Ruff passes. Initial sandbox execution
passed 620 and failed two existing loopback tests; the socket-enabled run passes
all. It captures no real profile and makes no model or remote-acquisition calls.

Mindgarden consumes that exact schema via `captured-source-bundle` 1.0.0,
media `application/vnd.mindcap.captured-source+zip`, manifest version `1`. Exact
membership/checksums, raw lineage, stable identities, locators, partial/empty
states and disabled capabilities are verified before normal plan/apply. Existing
UTF-8, archive, media and extension adapters remain on the same domain protocol.
No producer imports or new runtime dependencies enter the engine.

The schema/source pin is provisional until the owner draft is reviewed. A prior
package digest is retained as asserted lineage, not fetched or treated as a
deletion/delta command. Producer hashes do not authenticate its review authority.
Generic and actual-provider synthetic fixtures remain distinct evidence.

Branch/PR, functional revisions, exact verification, remaining parent scope and
the next action are recorded here and in CONTINUITY.md at each checkpoint.

Initial consumer verification: 6 new cases pass on each Python (1.181s/1.193s);
24 source/conformance/contract cases are rerun together. The actual two-capture
producer/consumer proof passes with acquisition blocked. The producer contract
is vendored with its exact SHA; core dependency metadata is unchanged.
