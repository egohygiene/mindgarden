# Shared CLI, API and web slice: review proposal

This is the bounded #47 handoff, not an implemented HTTP/web/worker product.
The issue explicitly says “After the ADR gate is accepted” and “do not choose
frameworks implicitly.” ADR-0009 and ADR-0016–0020 remain proposed with null
approval. No accepted framework, identity or runtime disposition is present.
The user authorized independent checkpoint work and preservation of genuine
blocks, not self-ratification. This proposal leaves those decisions reviewable.

## Existing shared services

The Python application/domain layer is already the common implementation.
Adapters should translate input/output and invoke these services, rather than
shelling out to the CLI, duplicating curation rules or querying canonical files
through a separate web model.

| User operation | Existing application service | Required authority / outcome |
| --- | --- | --- |
| Search, traversal, backlinks | `retrieval.search_payload`, `graph_payload`, `backlinks_payload` | Explicit live `QueryContext`; filter before ranking/traversal; final byte-budget and revocation check |
| Exact evidence | `evidence.resolve_evidence` | Exact source identity/revision, locator and content hash; no ambient source discovery |
| Context | `retrieval.render_context` | Explicit reviewed profile and readable scope; bounded JSON/Markdown; source text remains untrusted |
| Import | `ingestion.build_ingestion_plan`, `apply_ingestion` | Supplied artifact and local bindings; inspect exact digest; immutable original/normalized evidence |
| Review | `curation.build_curation_plan`, `apply_curation` | Supplied authored proposal, explicit human review authority and current digest; preserve source attribution |
| Route / canonical transitions | `routing.build_routing_plan`, `routing_lifecycle.build_transition_plan`, `RoutingPlan.apply` | Explicit catalog/gardens, private fallback, exact plan and recovery semantics |
| Preview/publication | `site.build_site` | Reviewed-public session; caller-owned output; Relay/consumer deployment authority remains separate |
| Vault recovery | `vault_recovery.build_vault_recovery_plan` | Explicit storage binding, checksum audit and reviewed recovery plan; no portable absolute location |
| Disposable query store | `domain.query_store.QueryStore` and the optional SQLite adapter | Already authorized view; exact scope/revision; no new canonical store |
| Dependency and memory exports | `dependency_builds.plan_build`, `memory.plan_memory` | Reviewed explicit inputs, exact dependencies, inherited sensitivity and immutable output bundles |

These are current callables, not a promised stable network API. Several write
handlers still translate argparse namespaces and need a typed transport-neutral
request/error envelope after the architecture gate. Transport-facing code must
not turn a supplied reviewer string or an untrusted prompt into authenticated
human authority. The existing single-user session file is not HTTP authentication.

## Proposed first slice and review contracts

The first implementation proposal is one bounded local application process with
a read/search/context experience and reviewable import/curation actions. This is
a proposal only: framework, browser client, identity mapping, bind/network policy,
process lifecycle, concurrency and worker execution require explicit disposition.
A background service is added only for a demonstrated need. SQLite stays optional.

Transport requests should carry a correlation ID, operation, explicit session
reference and represented revision; writes also carry a reviewed plan digest and
an independently authorized human approval. The controller resolves machine-local
locations outside portable records. Responses preserve existing canonical IDs,
provenance, effective scope, review/epistemic state, output budgets and fixed error
codes. They do not expose raw provider exceptions, denied identifiers, private
counts or host paths. No ambient registry-wide search is added by an API adapter.

A preview response grants no apply, publication, declassification or network
capability. Every request and queued operation revalidates expiration/revocation
and exact represented inputs; queue admission alone cannot authorize later work.
Cancellation/partial failure retains inspectable recovery state and immutable
originals. A web form cannot edit generated output and promote it to evidence.

## Parity and failure acceptance matrix

| Scenario | Common expected outcome across CLI/API/web/worker |
| --- | --- |
| Same authorized search/context request | Equivalent selected IDs, order, scoring reasons, source references, review and scope within the same budget |
| Replayed reviewed write | Verify the existing desired state; no duplicate sources or overwritten original |
| Source/policy/reviewer changes after preview | Stale plan or revoked authority; no consequential apply |
| Denied canary, expired session or lower public ceiling | Excluded before ranking/traversal and absent from snippets, counts, backlinks, caches and diagnostics |
| Interrupted operation/restart | Existing journals or owned partial artifacts remain inspectable; no fabricated success |
| Missing model, Google, database or network | Useful local reference workflow; explicit unavailable optional capability |
| Delete disposable projections / restore vault | Rebuild through portable canonical records and exact evidence; source identities remain stable |
| Keyboard/mobile/reduced-motion/nonvisual graph | Equivalent accessible operations, explicit status/focus and source links; no graph-only workflow |

Existing CLI/library and offline synthetic tests prove portions of the common
services. They do not prove HTTP authentication, UI accessibility or worker parity.
No new framework test suite is invented before its reviewed implementation exists.

## Runtime and consumer ownership

Realm #20/#34 owns Compose/devcontainer/service composition, volumes, ports,
health/resource limits, start/stop and clean-machine lifecycle. Mindgarden owns
engine contracts and review/recovery operations. Relay #40 owns shared `/garden`
build orchestration; Relay's existing Decisions renderer is reused. Aether #69
owns scoped agent-session capabilities, and Hygiene #61 owns cross-repository
steering. Their open acceptance is not silently replaced by local policy IDs.

The first consumer is a synthetic Ego Hygiene profile. A second synthetic
organization changes only documented owner IDs, garden IDs, URIs and local
bindings; it must reproduce the same engine outcomes without implementation copies.
Real Incompris configuration and content require a separate private consumer
checkpoint after the first usable setup. No private topology is inspected here.

## Exact next action

Review/dispose the relevant architecture proposals through the repository decision
process, including framework/auth/runtime and the ordinary/confidential boundary.
Once accepted source revisions are available, implement one read/query/review
transport slice through the services above, obtain Realm's compatible clean-start
profile, then run the parity/lifecycle/accessibility matrix. Until then #47 stays
blocked; this draft preserves the concrete design and remaining acceptance.
