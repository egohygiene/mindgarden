# Target architecture: decision and ownership map

This is the reviewable #42 checkpoint for [the #40 product destination](https://github.com/egohygiene/mindgarden/issues/40).
It records proposals and their prerequisites; it does not ratify architecture or
implement a new product stack. The current CLI and bounded local proofs remain
usable. The [six-draft map](garden-experience-milestone.md) separates source,
local tests, hosted checks, review and merge state.

## Decision state and precedence

Explicit user authority, repository policy, accepted architecture and owner
contracts govern implementation. Proposed ADRs do not become accepted because a
draft is tested or merged. ADR-0007–0021 retain `status: proposed` and
`approval: null`. Their implementation fields describe their individual scope;
existing reference behavior is evidence, not ratification of a future adapter.
No new accepted or rejected decision is recorded by this checkpoint. Alternatives
discussed in proposals are not independently ratified rejections.

Legacy ADR-0001–0006 retain their original labels in DECISIONS.md. Their human
authority/lineage migration remains #41; this document does not rewrite that
history. Hygiene's pinned [decision policy](decisions/policy-reference.json)
governs new records. Human disposition must preserve rationale, approver, affected
contracts/repositories and implementation-issue links through that process.

## Coverage of the ten required decisions

| #42 topic | Proposed ADR | Current implementation evidence | Remaining decision/proof |
| --- | --- | --- | --- |
| 1. Canonical ownership and source precedence | [0007](decisions/ADR-0007-portable-consumer-knowledge.md), [0010](decisions/ADR-0010-local-scope-and-review-authority.md) | Consumer-owned portable records; scope/review/routing contracts on main | Cross-owner disposition with Hygiene #61/Akashic #174; #48's two approval flows |
| 2. Originals and large assets | [0008](decisions/ADR-0008-immutable-source-vault.md) | Filesystem content identity/audit/export/restore/relocation, exact evidence | #35/#45 full media/provider/encryption and capture handoff acceptance |
| 3. Shared services/interfaces | [0009](decisions/ADR-0009-shared-local-application-services.md) | CLI calls Python domain/application services; renderer/storage adapters | API/web/worker parity under #47; framework/auth decisions |
| 4. Canonical versus disposable stores | [0007](decisions/ADR-0007-portable-consumer-knowledge.md), [0011](decisions/ADR-0011-public-federation-projections.md), [0016](decisions/ADR-0016-query-store-baseline.md) | Deterministic lexical/graph/context/public projections | Generic dependency manifests under #37; optional store parity |
| 5. Query-store baseline | [0016](decisions/ADR-0016-query-store-baseline.md) | Dependency-free JSON/lexical reference | #32 port/SQLite benchmark after disposition; #33/#34 optional |
| 6. User/collaboration/tenancy | [0017](decisions/ADR-0017-local-user-and-tenancy-boundary.md) | Explicit local single-user/single-writer baseline | Identity, membership, sync/conflict and tenant threat model before expansion |
| 7. Minimal topology and Realm | [0018](decisions/ADR-0018-minimal-runtime-topology.md) | Python core; optional prepared pinned Node/Quartz | Realm #20 released profile; minimal authenticated self-host decisions |
| 8. Jobs/lifecycle/retention | [0019](decisions/ADR-0019-bounded-operations-and-retention.md) | Digest-bound plans, owned outputs, bounded rollback/recovery | #46 contracts/proof; #37 invalidation; no deletion or queue adoption |
| 9. MCP and agent authority | [0020](decisions/ADR-0020-agent-interface-authority.md) | Scoped CLI reads/context, expiration/revocation, exact evidence | Aether #69 integration and synthetic CLI/transport parity before any endpoint |
| 10. Build versus integrate | [0021](decisions/ADR-0021-build-versus-integrate.md) | Optional Obsidian profile and pinned Quartz baseline | Per-candidate evidence/licensing/exit proof; no additional dependency adopted |

Public site, design, registry and composition boundary proposals are separately
recorded in ADR-0012–0015. They do not select the broader application framework.

## Canonical, generated and control ownership

| Layer | Source of truth and owner | Derived/control boundary |
| --- | --- | --- |
| Captured artifact | Mindcap/supplying producer owns capture fidelity, identity and package contract | Mindgarden consumes supplied captures; it does not silently acquire remote data |
| Original bytes/attachments | Consumer's explicit private vault owns immutable content | Content hash is distinct from logical artifact ID and physical location; provider credentials stay local |
| Normalized text/segments | Mindgarden adapter records deterministic transform/version and exact evidence | Original and normalized hashes/locators remain separately verifiable; normalization is not review |
| Reviewed knowledge/claims/synapses | Each repository, organization or person owns their portable Garden records | Human review records authority, attribution, uncertainty and contradictions; it does not assert universal truth |
| Archival reservoir | Athena owns its separate archive domain | An archive is a referenced source/integration, not a silently duplicated living Garden |
| Public resource catalog/Atlas | Akashic owns reviewed public Markdown/resources and stable IDs | Mindgarden indexes/references generated public projections; private cleanup cannot mutate Akashic |
| Query/index/graph/vector/UI store | Disposable Mindgarden or consumer projection | Exact input revisions, effective scope, rebuild/export/teardown are mandatory |
| Public site and portal | Checked static artifact; consumer owns final composition/deployment | Mindgarden owns output manifest/CLI; Relay owns reusable build mechanics |
| Registry/session/locations | Explicit machine-local consumer control | Membership labels, paths, credentials and authority digests do not enter portable/public lineage |

Existing local-path source records remain supported for compatibility and
synthetic fixtures. The proposed private-vault boundary for originals does not
authorize moving or deleting real sources. Raw archives and attachments never
enter public output merely because their source metadata is referenced.

Source precedence is typed rather than a global last-write rule: original bytes
establish what was captured; normalization establishes a reproducible rendering;
reviewed records establish a consumer's current interpretation. Conflicting or
superseded evidence stays explicit. Repository/organization discovery references
personal/restricted gardens only through authorized views; it cannot take their
ownership. Public curated knowledge requires its own approval, not a weaker
classification inherited from a destination name.

## Repository and runtime responsibility map

This reconciles existing SYSTEM.md with the live Hygiene #61, Mindgarden #40/#42
and Akashic #174 requirements. These are ownership pointers, not mutable runtime
dependencies or claims that every owner has accepted its integration.

| Owner | Responsibility and handoff | Boundary retained here |
| --- | --- | --- |
| Hygiene | Normative information flow, architecture/decision policy and cross-repository ownership | Local policy fixtures do not complete Hygiene #39/#61 |
| Mindgarden | Semantic contracts, normalization, curation, routing, retrieval/context and federation | Consumer records stay consumer-owned; no agent/runtime/provider takeover |
| Mindcap | Faithful capture, verified bundles and source/delta handoffs | Capture approval does not approve knowledge/publication |
| Akashic | Public curated resource knowledge and Atlas | Independent sanitized candidate intake/review; no private browser history |
| Athena | Archival reservoir | Referenced evidence, separate archival ownership/retention |
| Aether | Agent instructions, skills and bounded provider-neutral session capabilities | No self-granted tools, gardens, budgets, network or export authority |
| Realm | Local/self-hosted provisioning, Compose, runtime/model gateways and lifecycle | No duplicate Garden engine; host isolation needs its own proof |
| Relay | Pinned validation/build/publication orchestration | Does not select content or grant publication authority |
| EgoLint | Shared lint/validation mechanics and release-convention checks | Mindgarden remains owner of semantic validation rules |
| Pace | Reviewed convergence and human-owned live focus queue | Activity is evidence, not automatic strategic priority |
| Observatory | Read-only normalized evidence, freshness and projections | No remediation, privacy or content-ownership authority |
| Holon | Materialize pinned contracts/scaffolding | No live Garden database or copied engine |
| Identity | Brand/design authority and reusable identity sources | Mindgarden tokens are a proposed local consumer; no brand ratification claimed |
| RenderFlow | Rendered design/documentation experiences | Output remains derived; no private source access by default |
| Flow | Product/process intake and workflow coordination | Consumes contracts; does not become canonical semantic storage |
| Organization `.github` | Organization coordination and aggregate projections | Links to owner issues; no duplicate policy or issue state |
| Beacon | Optional packaging/distribution of a real publication artifact | No publication dependency for the local knowledge workflow |
| Human consumer/maintainer | Review, declassification, cleanup, publication and merge decisions | Agent implementation and passing tests never replace this authority |

## Two independently approved reference journeys

The implemented finite archive journey is captured original → normalized evidence
→ authored curation → reviewed prompt-bank record → scoped exact-citation search
→ bounded context → vault relocation/rebuild. Its synthetic evidence is linked
from [the private workflow proof](private-garden-evidence.md). Aether-governed
execution and feedback into new reviewed proposals follow as separate capabilities;
the context pack cannot grant its consumer tools or write authority.

The bookmark journey remains proposed under #48:

1. Consume a verified Mindcap bundle/delta through its actual versioned contract.
2. Plan private reconciliation, duplicate/near-duplicate grouping and quarantine.
3. Obtain cleanup approval; emit a reversible browser-import projection without
   silently changing originals or the live browser.
4. Separately propose per-item sanitized publication candidates, excluding private
   folders, notes, timestamps, session/account metadata and aggregate existence.
5. Obtain independent publication approval through Akashic's actual intake contract.
6. Validate and create a draft PR; a human merge changes canonical public catalog.
7. Consume a rebuilt public Garden projection by stable Akashic IDs/revisions.

Cleanup approval grants no publication authority. Publishing a resource does not
approve private deletion. Removing a personal bookmark never deletes its public
catalog counterpart. These requirements are not claimed as a completed #48 proof.
Unavailable/incompatible producer/intake contracts remain explicit gaps rather
than invented formats.

## Deferred choices and revisit triggers

No deadline below grants adoption authority; it triggers another evidence review.
Revisit at the stated event or by **2027-01-01**, whichever comes first.

| Choice | Evidence needed before decision | Owner/trigger |
| --- | --- | --- |
| SQLite query adapter | Scoped reference parity, representative synthetic corpus, latency/size/resource and rebuild/failure measurements | Mindgarden #32; before store implementation |
| CozoDB/Meilisearch/vector stores | Workload benefit over baseline, exact pins/licenses, privacy/cost/operational and removal evidence | #33/#34, organization search #478; measured baseline limit |
| API/web framework, editor, authentication | Selected single-user wedge, interface parity, security/accessibility and identity lifecycle | #40/#47; before framework or private network endpoint |
| Collaboration/multiple writers/tenancy | Membership, conflict/sync, revocation, audit, export/deletion and host assurance | #47, Aether/Realm; before second writer or shared access |
| Worker/queue/scheduler | Bounded job/checkpoint contract, cancellation/recovery and resource need | #37/#46, Realm; before recurring background work |
| MCP transport/SDK | Aether #69 compatible capability handoff, read parity and denied-escalation fixtures | Aether/Mindgarden #51; before endpoint/adapter adoption |
| SilverBullet | Pinned synthetic authoring/export experiment and license/identity/scope/exit evidence | #42/#47; before integration/code reuse |
| AFFiNE | Pinned synthetic editor/export experiment and collaboration/ownership/exit evidence | #42/#47; before integration/code reuse |
| Papra | Realm #41 pinned lab, document corpus, current immutable license/reuse review, provenance/export/removal results | Realm #41; before importing code/assets or documents |
| OpenViking | Pinned context/retrieval experiment and canonical/projection/privacy/exit evidence | #42; before adapter adoption |
| Cognee | Pinned graph/memory experiment and provenance/invalidation/privacy/exit evidence | #42/#49; before adapter adoption |
| Destructive retention | Accepted policy, explicit human plan, hold/backups/deletion-verification and recovery limits | Hygiene, #45/#46; before any deletion implementation |

## Dependency-ordered next work and retained gates

1. Human disposition of the focused ADRs and #41's authority migration precedes
   consequential broader-product choices. Reconcile Hygiene #39/#61, Akashic #174
   and Aether #69 at their owners; local proposals do not replace those contracts.
2. #46 may deliver an authored synthetic contract/local checkpoint now; full
   private-pilot proof depends on #20. #37's generic dependency work can consume
   those requirements without making every learning/memory output a prerequisite.
3. After ADR-0016 disposition, #32 implements a small scoped adapter/parity slice.
   Optional #33/#34 experiments follow an actual workload; they do not gate core.
4. After shared-service, tenancy/runtime/auth/interface decisions, #47 implements
   one paid-service-free CLI/API/web slice through Realm/Aether seams. No framework,
   model gateway or authenticated server is selected by this document.
5. #48's synthetic contract work depends on the actual capture/intake boundaries;
   a private pilot and public PR each need their own explicit approval.
6. #20 consumer/publication evidence and #19 release gates remain distinct from
   the finite offline proof. Relay #40 action and host promotion are not completed
   by the local compositor. #43/#44 own decision publication and typed projection.

All 38 issues remain represented in [the coverage ledger](open-issue-coverage.md).
#42 remains partial: human ratification, full cross-owner disposition, bookmark
proof and an implementation roadmap derived from **accepted** decisions are still
required. The conditional sequence above is proposed until those decisions exist.
