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

### #11 review receipt

[Mindgarden #113](https://github.com/egohygiene/mindgarden/pull/113), branch
`feature/11-captured-bundle-handoff`, functional `b661dc2`, stacks over #112.
The 24-case combined adapter/conformance/contract run passes in 3.857s.
Next: v2 archive compatibility, followed by the optional extraction producer.

### #15 direct historical-profile reader

Branch `feature/15-archive-v2` stacks over #113/`7230118`. Authoritative v2.0.0,
v2.0.1 and v2.0.2 were reread through the authorized source connector; private
specification bodies are excluded. Tests use an authored v2 envelope over the
existing synthetic preservation-schema 2.0 records. Both ZIP packaging passes
are reopened and inventories verified. All three versions support independent
asset selection; overlapping v2/v3 observations retain evidence identities.

18 archive cases pass on Python 3.12/3.13 (5.860s/6.052s). The 12-case private
workflow/compaction run passes (28.972s). Adapter version 1.2.0 changes only the
documented derived metadata/view hashes in three proof goldens. No evidence,
body, review, byte budget or vault backup fact changes. Full producer conformance,
collections/multipart and real consumer adoption remain open. Next: #13 producer.

[Draft #114](https://github.com/egohygiene/mindgarden/pull/114), functional
`cc38583`, records the #15 checkpoint. Mixed-vault proof passes (1 case,18.956s).

### #13 optional extraction checkpoint

Branch `feature/13-extraction-producer` stacks over #114/`4c80d08`. Versioned
requests and outputs connect an optional producer to existing unreviewed curation
plans. The offline recording adapter, exact source grants, six-state recovery,
per-unit checkpoint callback and immutable private CLI bundle preserve review
separation. A synthetic v2 conversation, two captured bookmarks and a page excerpt
prove attributed proposals → authored review → rebuilt search/graph. Ambiguous
entities/unknown predicates stay unresolved, with conflicts and negation retained.

13 extraction/wire/schema cases pass on Python 3.12/3.13 (28.043s/26.264s).
Ollama's current official docs were read; pure schema/chat mapping and a synthetic
loopback-only opt-in probe are provided. No executable or operator-selected local
model exists here, so only the dry run is tested and accuracy remains unmeasured.
Private source grants remain offline; network-provider policy is an explicit gate.
No new runtime dependency or ADR acceptance is introduced. Next: #14 lifecycle.

[Draft #115](https://github.com/egohygiene/mindgarden/pull/115), functional
`82f83fe`, records the #13 checkpoint. Eight new cases pass again after source
metadata retention (27.623s). Historical whole-tree Ruff has 35 existing unused
import/variable findings; focused changed-code lint passes.

### #14 reviewed graph moves and v2 lifecycle

Branch `feature/14-routing-lifecycle-v2` stacks over #115/`eed15a1`. Private moves
retain exact outgoing graph data, review, authors, evidence and qualifications.
The unchanged v1 request/event schemas remain supported; explicit v2 adds reviewed
split anchors and replacements with exact authored lineage. Originals remain
immutable and old references resolve to one canonical successor. Tests reject
conflicts, stale children, missing lineage and policy weakening, and recover after
a second-garden cutover fault. 23 routing/schema cases pass on Python 3.12/3.13
(16.513s/15.844s). ADR-0022 is extended as a proposal, with no approval change.
Incoming edge retargeting, public/policy-changing and broader platform acceptance
remain open. Next: #12 projection matrix, narrowing and larger measured corpus.

[Draft #116](https://github.com/egohygiene/mindgarden/pull/116), functional
`f369932`, records the #14 checkpoint. Next: #12, then #16.

### #12 projection coverage and explicit narrowing

Branch `feature/12-projection-selection` stacks over #116/`f9219da`. All eight
relation types, directed/undirected backlinks, cross-garden references, exact
claim evidence and suppressed denied/unavailable endpoints are tested. Existing
session authority can be narrowed before root probing or body reads, with a
selection-specific cache identity. Omitted cross-garden dependencies fail on the
original revision pin; no new authority or replacement pin is manufactured.

9 matrix/selection/corpus cases pass on Python 3.12/3.13 (19.377s/18.607s).
`python scripts/projection_benchmark.py --workspace .cache/pipeline-next/corpus-2048
--records 2048` passes the same 60-second/256-MiB reference limits. Six projections
take 15.282–28.402s and peak RSS is 166,473,728 bytes. A fresh-context index and
JSON-context repeat matches both exact hashes (16.150s/27.462s). Reports are
committed under tests/fixtures/projection-corpus. This is observed CLI performance,
not interactive/UI or arbitrary-hardware acceptance. No new cache/database/model
is introduced. Next: #16 private/local discovery and progressive selected retrieval.

[Draft #117](https://github.com/egohygiene/mindgarden/pull/117), functional
`2c70c89`, records the #12 checkpoint. Next: local discovery over the same authority.
