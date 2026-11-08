# Open-issue coverage — 2026-11-06

This is the detailed coverage ledger for [ROADMAP.md](../ROADMAP.md). It records
all **44 open issues**: the original 38-issue queue and six newly deferred
items #86–#91. Live bodies/comments and the merged #74–#85 baseline were refreshed
for the new phase; earlier merge receipts preserve their original observations. It preserves each issue's acceptance
criteria; a batch is a bounded checkpoint, not automatic parent completion.

## Observed baseline and authority

Current main is `b9cc3fd3b8b68e56944d592e2092b07485de465a`, after the
[authorized #74–#85 merges](merged-pipeline-storage-checkpoints.md). The engine's
combined suite passes 298 tests on each supported Python; exact-source/installed
proofs and passing pre-merge CI remain linked in those receipts. The original 38
issues remain open and retain their acceptance. All ADRs remain proposed/null
approval. New #86–#91 are a **deferred post-queue cohort**, not the next active
batch. [Their roadmap](deferred-context-package-roadmap.md) records scope,
existing owners and the end-of-roadmap reconciliation/scheduling gate.

The older baseline and draft observations below are historical evidence.

Merged main: `9fae752b3cf7eb9c74033a72a12d125c42f8659e`. Its tree is exactly
`a381b8bea2270b6ebd41a8bbe205d5f0a6f3e188`, the tree of the tested combined
checkout `b82520b883b86be70bc939302411a0fb8587aab2`. All thirteen PR heads had
successful automatic Test runs, no submitted reviews and no unresolved threads.
The maintainer explicitly authorized merging the stack; that instruction does
not ratify ADR-0007–0010. They remain **proposed**. All 38 parent issues remain open.

Before merging, both `.venv/bin/python -m unittest discover --start-directory tests`
and `.cache/python313/bin/python -m unittest discover --start-directory tests`
passed **139 tests without skips** (Python 3.12.14 and 3.13.5). The unchanged-tree
comparison after merge passed. These are local checks, distinct from the thirteen
successful hosted head checks. No workflow was manually dispatched.

[The private-workflow evidence](private-garden-evidence.md) records the synthetic
archive → reviewed prompt → exact evidence → bounded context → vault relocation
proof. A bounded synthetic proof does not establish real-consumer, publication,
confidential-runtime, platform, release or complete product acceptance.

| PR | Merge commit | Original head |
| --- | --- | --- |
| [#52](https://github.com/egohygiene/mindgarden/pull/52) | `4a18d51aebff7a1293a4252dac58c3f21479a6a9` | `e137ef0` |
| [#53](https://github.com/egohygiene/mindgarden/pull/53) | `834f8c874d62cf04be20706d8f23d701f2e2ba34` | `1f37f56` |
| [#54](https://github.com/egohygiene/mindgarden/pull/54) | `fdd990875aae1cf5125e8b31e3ba633596fcfdf7` | `b93969c` |
| [#55](https://github.com/egohygiene/mindgarden/pull/55) | `39cef64f6f6ebe330a9d95fda36d35434eadc3f8` | `dd4be16` |
| [#56](https://github.com/egohygiene/mindgarden/pull/56) | `a35e2aec3cea7b7567e5bbbd876f56907d7f119b` | `febb2b0` |
| [#57](https://github.com/egohygiene/mindgarden/pull/57) | `d8c44800741007dddecc73812e296fdb4eee95fa` | `f655d03` |
| [#58](https://github.com/egohygiene/mindgarden/pull/58) | `298411eaa80f3b9f23c643a7367930c8379cfac3` | `8836fdd` |
| [#59](https://github.com/egohygiene/mindgarden/pull/59) | `f2e43fd70bad2f5dac0c4d381db077001d42a49b` | `1a49992` |
| [#60](https://github.com/egohygiene/mindgarden/pull/60) | `1c58c561be747271417040a339f64e1f3e6e9bf4` | `fb3bcf3` |
| [#61](https://github.com/egohygiene/mindgarden/pull/61) | `5251abda4397ca7cbd1f83261ef90a7cd99225ec` | `df724c4` |
| [#62](https://github.com/egohygiene/mindgarden/pull/62) | `26f17c386c07be43ed39bb1721a370bc586f8477` | `e31d574` |
| [#63](https://github.com/egohygiene/mindgarden/pull/63) | `7b6537dfc269042cab3321bc081ece3c8e5a2ae7` | `afbd420` |
| [#64](https://github.com/egohygiene/mindgarden/pull/64) | `9fae752b3cf7eb9c74033a72a12d125c42f8659e` | `b82520b` |

## Readiness and proposed batches

`ready` means the stated next checkpoint can proceed; `partial` means some parent
scope is implemented with remaining work; `blocked` names a missing contract,
decision or proof; `deferred` is deliberate scheduling; `umbrella` coordinates
children. Ready never means fully accepted. These batches express dependencies,
not one serial gate over all work.

| Batch | Bounded deliverable and exit evidence |
| --- | --- |
| B0 | Reconcile the merged stack, all open issues, proposed decisions and this ledger. No parent closure. |
| B1 | #16 local descriptor/public-projection contract, checksums and deterministic synthetic catalog; reviewed-public leak negatives. No deployment or remote acquisition. |
| B2 | #30 non-destructive registry lifecycle over existing bindings and B1 identity/version contracts; explicit platform support and isolated union-view fixtures. Accepted architecture controls consequential extensions. |
| B3a | #17 public `/garden` renderer checkpoint after B1, preserving the pinned Quartz boundary; accessibility and empty/failure fixtures. |
| B3b | #18 caller-owned portal build/composition after the relevant #17 artifact contract; Relay integration separately pinned and verified. |
| B4 | #20 consumer checkpoints, one at a time: synthetic publication proof, approved private legacy pilot, then pinned Empathy consumption through its owner. |
| B5 | #19 release readiness after B4 and release acceptance. Actual release/registry publication requires separate authorization. |
| R0 | #46 compaction/retention policy and schema proposal early; preserve originals and separate retention classes. Full compaction/private pilot waits for its evidence and decisions. |
| R1 | #37 generic dependency-build/observation contract, then separate #49 memory and #28 learning projection checkpoints. |
| D | #41/#42 decision disposition/adoption, then #43 publication and #44 typed ADR projection, through shared owners. Independent of completing every 1.0 child. |
| Q | #32 adapter/SQLite baseline after B1, scoped inputs and accepted storage decisions; #33/#34 optional evaluations only after the baseline is measurable. |
| P | #40/#47 product discovery and accepted API/web/runtime decisions, then the shared-interface slice. #38 design tokens can proceed independently. |
| J | #48 synthetic bookmark contract/cleanup, then separately approved Akashic packet and consumer proofs; upstream contracts remain owned upstream. |
| L | #27 release-convention preparation can proceed independently; final shared-validator and publication evidence stays gated. |
| A | #51 two local provider-fixture recovery proof over supported scoped context contracts. No paid provider or full #47 application is required. |
| E | #26 reference evaluation; #21 post-1.0 infographic candidates and other explicitly optional experiments. |

## Dependency corrections proposed for review

1. Preserve the distinction in #5 between engine 1.0 and #40's broader product.
   The #40 comment's #41/#42 gate governs broader product choices. Historical ADR
   backfill, a full web application and completed fleet rollout are not blanket
   prerequisites for an offline engine/projection checkpoint. Decisions remain
   proposed until supported human disposition is recorded.
2. #16 needs the usable #10/#12/#14 contracts, now implemented in the merged
   stack. It does not require completing their unrelated consumer/media scope.
   Its descriptor contract precedes #30 federation integration and #32 imports.
   A local build does not satisfy hosting or Akashic acceptance.
3. #29 and #45 supplied prerequisite scope/content-reference contracts before
   ingestion/routing; the later #30 registry and #35 document proofs remain open.
   Retain the [milestone's original corrections](private-garden-milestone.md).
4. #18's **full** acceptance retains #17 and Relay dependencies. A caller-owned
   output contract may be proposed before final UI acceptance; this is not
   permission to claim a deployed portal or bypass #17's accessibility proof.
5. #20's local synthetic proof can advance before all publication consumers are
   ready. Full #20 still requires #16/#17/#18, the approved private legacy pilot,
   Aether/Relay and Empathy evidence. It must not depend on closing #1, whose
   acceptance itself includes Empathy. Empathy #65 explicitly records this cycle.
6. #46 policy requirements are considered before destructive retention or media
   lifecycle choices. Its #20/private-pilot dependency gates full proof, not early
   schema proposals. #49 must distinguish projection expiry from source deletion.
7. #51 is a conformance/recovery scenario over supported contracts. #40/#47/#49
   are related horizons, not automatic gates requiring a web app or live provider.
8. #27 can prepare a pinned release declaration/artifacts now. Open EgoLint #29
   retains fixture/dogfood acceptance; neither local builds nor closed upstream
   issues establish an approved release, PyPI availability or completed #19.

## Cross-cutting coverage

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#1](https://github.com/egohygiene/mindgarden/issues/1) — ecosystem knowledge contract/adapters | umbrella | V1 schemas/lifecycle; merged #53–#64 validation, sources, reviewed knowledge and context | Hygiene/catalog references, complete consumer acceptance and Empathy integration | HYG-04/EMP-05; children #10–#16/#20; B1–B4, avoid umbrella/consumer cycle |
| [#2](https://github.com/egohygiene/mindgarden/issues/2) — workstation/public projections | umbrella | V0 Obsidian/Quartz profiles and publication negatives; scoped v1 engine | V1 projection mapping, OpenWiki spike/disposition, deployed reviewed-public reference site | #1 contracts, Relay; B1/B3/B4, optional adapters distinguished |
| [#5](https://github.com/egohygiene/mindgarden/issues/5) — engine 1.0 delivery | umbrella | Extracted package/lifecycle plus merged private workflow proof | Publication/federation, real archive, golden consumer and reproducible release acceptance | Owning child contracts and evidence; B0–B5; broader product remains separate |
| [#37](https://github.com/egohygiene/mindgarden/issues/37) — evidence/observation/claim dependency builds | umbrella | V1 claims/provenance plus authored observation/dependency manifests, digest-bound builds and affected-output reconciliation | Broader canonical observation/validity integration, event-driven targeted execution, Mindcap capture and approved private pilot | #11/#12/#13/#16/#29; Mindcap #33, Hygiene #42; R1 after owning source contracts |
| [#40](https://github.com/egohygiene/mindgarden/issues/40) — self-hosted second-brain product | umbrella | Existing Python services/CLI and finite offline workflow; ownership proposals | Audience/product decisions, accepted ADR sequence, topology/auth/editor/API/web, complete lifecycle and accessibility proof | #41/#42 govern broader product, #47 and owner contracts; P, no blanket 1.0 gate |

## Architecture and decision lineage

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#41](https://github.com/egohygiene/mindgarden/issues/41) — historical ADR migration/continuous capture | blocked | Legacy ADR-0001–0006 preserved; #52 adds policy pin/index and proposed ADRs; #50 migration map predates stack | Complete evidence-backed history/disposition map, managed hook/shared CI, live Decisions publication | Hygiene #15 ratified and Holon #6 delivered; Relay #5/#27/#33 and Pace #5 still have adoption/acceptance gates; D, verify released inputs before backfill |
| [#42](https://github.com/egohygiene/mindgarden/issues/42) — target architecture ADR gate | partial | Proposed ADR-0007–0021 cover all ten topics; merged #72 decision/ownership map and conditional follow-ups; no new runtime under #42 | Human ratification, #41 lineage migration, full cross-owner disposition, #48 approval-flow proof and accepted-decision implementation roadmap | Hygiene #61/#39, Akashic #174, Aether #69; conditional #32/#47/#48 gates retained; D checkpoint |
| [#43](https://github.com/egohygiene/mindgarden/issues/43) — shared `/decisions/` view | blocked | Pinned shared read-only Relay preview caller in docs/product-checkpoints.md; no claimed deployed view | Pinned shared build/collector, represented lineage, composed preview, accessibility and public route proof | #41/#42, Relay #27/#30/#33, Holon #22, Observatory #7; D after compatible source/build contract |
| [#44](https://github.com/egohygiene/mindgarden/issues/44) — typed ADR knowledge projections | partial | Public-only versioned metadata/lineage/backlink/context adapter; exact owner read-model digest/revision; ADRs remain canonical files | Full narrative/inherited/private/federation/UI integration and real consumer proof | #41/#42/#12/#16/#29/#31 and Hygiene #15; D after B1 and supported ADR inputs |

## Privacy, scopes, registry and source vault

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#10](https://github.com/egohygiene/mindgarden/issues/10) — validation/private publication | partial | Merged version-aware validation plus merged #70 publication/preview hardening and reusable 80-test synthetic conformance pack; v0 preserved | Normative policy/runtime assurance, approved consumer/media conformance and complete cross-repository acceptance | Existing #7/#8/#9 contracts; #17 output surfaces; B3 conformance checkpoint, external owner gates retained |
| [#29](https://github.com/egohygiene/mindgarden/issues/29) — independent scope/sensitivity axes | partial | #55/#62 local versioned contract; merged #80 shared decision API/schema/CLI and inheritance fixtures | Normative organization policy, declassification/federation integration and verified restricted runtime | Hygiene #39, Realm #25 → #60, #10/#14/#16; local contract usable, external assurance blocked |
| [#30](https://github.com/egohygiene/mindgarden/issues/30) — local registry/private overlays | partial | #55/#62 bindings/scoped queries; merged #67 Linux lifecycle/views/recovery; merged #82 owned cache recovery; draft [#93](registry-native-platforms.md) adds ACL/path controls, 44 tests per native macOS job and clean installed-wheel goldens | Windows mutation, broader native hosts, verified restricted/encrypted coexistence and organization/host assurance | #29/#14/#16 contracts available; ordinary native proof independent of confidential assurance; Hygiene #39/#40 and Realm #25/#60 gate assurance; preserve originals |
| [#31](https://github.com/egohygiene/mindgarden/issues/31) — scoped retrieval/sensitivity | partial | #62/#64 filter before bodies/ranking; merged #81 output byte ceilings, live authority, sanitized diagnostics and owned caches; private asset output follows the same contract | Full federation/consumer projections, normative assurance/declassification and runtime integration | #29/#10/#12/#14, Hygiene #40 and Realm #25/#60; carry invariants into B1/B2/Q |
| [#35](https://github.com/egohygiene/mindgarden/issues/35) — confidential document/PDF ingestion | partial | Draft #83 ordinary synthetic PDF checkpoint: versioned bundles/page spans, explicit initial classification, optional Poppler 25.03.0 and six real parser states | Confidential encrypted runtime/temp assurance, OCR/office/complex layout and real consumer proof | #29/#10/#11 local boundary usable; Hygiene #39/#40 and Realm #25/#60 still gate restricted processing |
| [#45](https://github.com/egohygiene/mindgarden/issues/45) — portable private source/media vault | partial | #56/#63/#64 immutable vault/recovery; merged #84 adds versioned asset manifests, opaque media, retained-original review, explicit storage factories and archive/PDF/media recovery golden | Approved-copy rights policy, timed/destructive retention, encrypted/provider/platform/power-loss acceptance and real private consumer integration | #11/#15/#30/#31/#35/#40/#42; R0 early, later local/media checkpoints and independent adapter proofs |

## Ingestion, curation, routing and retrieval

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#11](https://github.com/egohygiene/mindgarden/issues/11) — normalized-source extension boundary | partial | #57/#60 plus merged #74 versioned adapter declarations, bounded conformance harness, immutable observation and reference extension fixtures | Provider-neutral Mindcap #35 wire contract, real producer handoff and wider adapter corpus | #8/#9/#10; Mindcap #35/#48 for bookmark proof; J; capture/model producer stays separate |
| [#12](https://github.com/egohygiene/mindgarden/issues/12) — graph/search/bounded context | partial | #58/#62/#64 plus merged #78 outbound links, eight-projection golden/schema matrix, selected redaction provenance and measured 1024-note corpus | Wider graph-type/cross-garden consumer matrix; larger corpus/runtime envelopes beyond the measured local reference | #8/#9/#10; B1 public output, Q performance; no database needed for current workflow |
| [#13](https://github.com/egohygiene/mindgarden/issues/13) — reviewable curation/extraction plans | partial | #59/#64 plus merged #75: merge qualification/author inheritance, exact relationships, selected claim evidence and authored redactions | Wider independent media/multi-route proofs; optional versioned entity/triple producer with failure/resume/evaluation fixtures | #9/#10/#11; J and optional producer checkpoint; no model prerequisite for authored plans |
| [#14](https://github.com/egohygiene/mindgarden/issues/14) — canonical routing/private fallback | partial | #61/#63/#64 plus merged #77 append-only private move/merge transitions, aliases, one retrievable home and recovery | Public/policy-changing and attached graph transfers, split reconciliation, full registry/organization acceptance | #9/#10/#12/#13; B1 descriptors then B2 registry; no public default from missing fallback |
| [#15](https://github.com/egohygiene/mindgarden/issues/15) — conversation archives/selective assets | partial | #60/#64 plus merged #76: v1.2.1 minimal reader, v3.2.2/v3.2.3 profiles, selective attachment catalogs/bytes, opaque JSON attachment proof | v2.0.1 reader/fixtures over inspected v2.0.0 baseline; collections/multipart, wider media and full producer conformance | #11/#13, Mindcap #31; B4 historical compatibility only after authoritative specs; do not infer old-version support |

## Projections, federation and portability

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#16](https://github.com/egohygiene/mindgarden/issues/16) — descriptors/federated discovery/agent projections | partial | Merged #66 plus merged #79 pinned rendered-site adapter, portable data-only package references and explicit catalog refresh states | Private/internal federation, signatures/authentication, remote refresh/acquisition, package installation and real Akashic/Aether consumer proof | #10/#12/#14 implemented contracts; #17 bridges rendered routes, Akashic #176 and Aether #69 integration later |
| [#18](https://github.com/egohygiene/mindgarden/issues/18) — composable portal builds | partial | Merged #71 local compositor pins represented revision and actual manifest, preserves siblings and writes checked ownership receipt; authored and actual 60-file Quartz proof | Pinned Relay #40 action, Empathy migration, host promotion/rollback and production acceptance | #17 output contract; Relay #4/#40 independent integration gates; B3b local checkpoint |
| [#49](https://github.com/egohygiene/mindgarden/issues/49) — assistant-memory snippets | partial | Versioned reviewed memory plans/projection, seven actions, explicit budgets, copyable exports, staleness/privacy fixtures and generic publication draft | Richer interactive review, provider-specific tokenizers/integration and automatic consumer refresh/revocation | #46 owning retention contract, #16 and #15 related; R1 bounded projection active; provider-neutral, no source deletion |
| [#51](https://github.com/egohygiene/mindgarden/issues/51) — provider-switch recovery scenario | partial | [Provider continuity proof](provider-switch-proof.md) removes the first local adapter/cache, rebuilds exact scoped context through the second, and preserves decision/correction history; current draft verification is in the release ledger | Finish exact compatibility/installed-engine verification and maintainer review; no live provider account required | Supported #16/#45/context contracts; #47/#49 related rather than whole-application prerequisites; A, then #27 preparation |

## Design, shared services, API and web

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#38](https://github.com/egohygiene/mindgarden/issues/38) — stack-neutral design tokens | partial | Versioned token/schema source, visual/image/diagram references, offline CLI exports and optional revision-bound Quartz/CSS consumer merged through #69 | Human design disposition, additional consumers and complete accessibility evidence | Independent P/design checkpoint after #68 for review convenience; selects no frontend framework |
| [#17](https://github.com/egohygiene/mindgarden/issues/17) — public Obsidian-like /garden | partial | Merged #68 scoped literal v1 output, exact citations, selected links/search/graph and pinned offline Quartz/loopback preview; #69 mobile correction | Full WCAG 2.2 AA, large-corpus/real-consumer acceptance and richer content/assets | Existing #10/#12/#16 contracts; #38/#10/#18 draft checkpoints; distinct from #47 authenticated application |
| [#47](https://github.com/egohygiene/mindgarden/issues/47) — shared CLI/API/web product slice | blocked | Concrete shared-service/transport/parity proposal plus existing Python application services; no HTTP/web/worker adoption | Accepted runtime/framework/identity ADRs, API/web/worker parity, editing/media, Compose lifecycle/accessibility and two-organization canaries | #40/#42/#43/#44/#45/#46/#10–#15/#29–#32; Realm #20/#34, Relay #40, Aether #69; P in bounded slices after actual contracts |

## Bookmark/reference journey

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#48](https://github.com/egohygiene/mindgarden/issues/48) — private bookmark cleanup/separate Akashic publication | partial | Bounded normalized v0.1 metadata cleanup, digest-bound resumable review, preserved originals, cleaned JSON/HTML and explicit unavailable public handoff | Accepted source-bundle/delta and Akashic intake/freshness contracts, raw capture verification, real canonical URL integration and cross-source knowledge proof | #42/#11/#13/#14/#16/#29/#30/#31, Mindcap #35, Akashic #173–#176; J contracts/fixtures first; metadata-only mode remains useful |

## Consumer, packaging and release readiness

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#20](https://github.com/egohygiene/mindgarden/issues/20) — complete archive/Empathy golden path | partial | #64 plus `5cb8359` composed source/wheel golden, scoped private-pilot helper and Empathy draft #120; exact references survive relocation | Approved real legacy archive/review/selected media, strict Empathy entrypoint cutover and holistic acceptance, actual renderer/deployment; synthetic public federation is proved | #7–#18 contracts/proofs, Aether #51, Relay #40, Empathy #65; B4 staged, no private content in this repository |
| [#27](https://github.com/egohygiene/mindgarden/issues/27) — Python release-convention pilot | partial | Draft #95 adds pinned declaration/changelog/Taskfile/manual Relay flow, one version authority and reproducible source/wheel/checksum/SBOM/provenance/status bundles; 315 tests per Python | Qualified Relay root-pyproject schema correction, broader EgoLint Python conformance, actual approved immutable release and external signing/PyPI evidence | Aether #61, Hygiene #27, Relay #46/#47 closed; EgoLint #29 remains partial; L preparation can proceed, final conformance/publication separate |
| [#19](https://github.com/egohygiene/mindgarden/issues/19) — reproducible 1.0 release | deferred | Dependency-free package and v0 compatibility; local reproducible private-workflow proof | Full 1.0 acceptance, clean released-version consumption, reproducible artifacts/guides/threat model, reviewed GitHub/PyPI OIDC release and Empathy pin | #20, Empathy #65, Relay #4, #27 convention; B5 deferred by maintainer (ordinal 21); resume after organization release conventions |

## Query stores and optional evaluations

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#32](https://github.com/egohygiene/mindgarden/issues/32) — replaceable query-store/SQLite baseline | partial | Opt-in SQLite FTS5 port/capabilities, reference scoring parity, audit/backup/restore/reset and 256-note observation | Incremental updates, larger workload/resource/platform/confidential proof and accepted permanent store disposition | #12/#16/#31, Realm #25/#60 and accepted #42 storage decisions; Q after B1, canonical files remain authoritative |
| [#26](https://github.com/egohygiene/mindgarden/issues/26) — OpenAleph architectural evaluation | deferred | Evaluation question set only; no dependency adopted | Versioned evidence-backed adopt/adapt/reject matrix, privacy/license/cost analysis and optional synthetic export experiment | Related #11–#17, no required gate on deterministic engine; E independently when selected |
| [#33](https://github.com/egohygiene/mindgarden/issues/33) — optional CozoDB projection evaluation | deferred | No CozoDB dependency or conformance claim | Exact-version/license/platform evidence, removable adapter, scoped corpus and resource/recovery measurements | #32 baseline, #26 related, Realm #25/#60; Q optional after baseline; rejection is valid |
| [#34](https://github.com/egohygiene/mindgarden/issues/34) — optional OpenViking context projection | deferred | No OpenViking dependency or conformance claim | Exact-version/license/network/model/telemetry tests, scoped removable adapter and comparative lifecycle/resource evidence | #32/#12, #26 related, Aether #64, Realm #25/#60; Q optional; rejection never blocks core |

## Learning, insights, compaction and retention

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and next batch |
| --- | --- | --- | --- | --- |
| [#21](https://github.com/egohygiene/mindgarden/issues/21) — reviewed infographic candidates | deferred | Canonical claims/sources and authored review available; no rendering/publication adapter | Renderer-neutral candidate schema, claim-level privacy/rights, deterministic batches, downstream artifact feedback and negative fixtures | #13/#14/#16/#19; explicitly post-1.0 E; private `szmyty/garden` consumer remains separate |
| [#28](https://github.com/egohygiene/mindgarden/issues/28) — learning cards/summaries/review schedules | deferred | Reviewed source/context primitives; no learning-specific schema | Candidate/card/event/schedule contracts, authored no-model export/roundtrip, contradiction/privacy/refresh and accessible review proof | #9/#10/#12/#13; #17 for web rendering, Realm #20 for runtime; R1 contract/export can precede full UI if selected |
| [#46](https://github.com/egohygiene/mindgarden/issues/46) — hierarchical compaction/retention | partial | Merged #73 v1 plan/retention/manifest contracts, read-only scoped evaluator, authored archive→curation→retrieval/context proof and selective invalidation | First-pass raw-only compaction, large-corpus/semantic quality, persistence/expiry/deletion execution and approved private pilot; no destructive implementation | Existing #11/#13/#14/#15/#31/#45; #20 gates full pilot, not early contract checkpoint; R0 |

## Deferred context-package phase after the current queue

| Issue and purpose | State | Current evidence | Unmet parent criteria | Dependencies and proposed later batch |
| --- | --- | --- | --- | --- |
| [#86](https://github.com/egohygiene/mindgarden/issues/86) — reconcile composed AI/context-package phase | deferred umbrella | Filed proposal with five native sub-issues and a documented roadmap; no new runtime | End-of-current-queue reconciliation, overlap disposition, owner decisions and later activation | Existing 38 retain priority; D0, then choose bounded work only after maintainer scheduling |
| [#87](https://github.com/egohygiene/mindgarden/issues/87) — Drive capture/refresh and chosen garden locations | deferred | Source/vault/registry boundaries exist; connector and convenience orchestration are proposals | Provider contract, stable source revisions, duplicate-safe refresh/recovery and private storage profiles | #11/#13/#30/#35/#45/#47 and Mindcap capture; D1 after #86 gate |
| [#88](https://github.com/egohygiene/mindgarden/issues/88) — installable data-only context packages | deferred | #16 supplies pinned package/reference primitives; lifecycle not implemented | Versioned selection/lock, reviewed update/remove, conflict/permission and two-project proof | #14/#16/#29/#30/#31/#45/#51; D2a; Drive/RDF/model not mandatory |
| [#89](https://github.com/egohygiene/mindgarden/issues/89) — scoped AI research broker | deferred | Shared retrieval/evidence services exist; iterative research role not implemented | Bounded planner/tool interface, evidence/uncertainty, revocation, provider removal and measured quality | #12/#13/#31/#47/#51, Aether/Realm owner contracts; D3; local fixtures independent of Drive/packages |
| [#90](https://github.com/egohygiene/mindgarden/issues/90) — synthetic structured analysis and reviewed preparation packet | deferred | Generic context/recovery primitives only; no financial analysis or consumer data used | Exact ledger normalization, verified calculations, coverage, selected export and clean recovery | #11/#13/#29/#31/#35/#45; #32 only if justified; D4 local/model-disabled first |
| [#91](https://github.com/egohygiene/mindgarden/issues/91) — RDF/JSON-LD and PROV scoped packet evaluation | deferred | Captured standards/mapping proposal; current canonical formats unchanged | Versioned loss-aware mapping, offline contexts, scoped overview, denied graph/provenance and adopt/adapt/reject evidence | #12/#13/#16/#29/#31/#42/#45/#46/#49/#88; D2b; no automatic replacement or clearance certification |

## Retention requirements carried forward now

R0 must define separate retention for immutable source archives, durable reviewed
knowledge, disposable model/context/cache state, and publication artifacts. An
expired projection is not permission to remove source evidence or knowledge.
Supersession and discard-proposed are review states, not deletion instructions.
Every future prune/garbage-collection operation needs an exact-input reviewed
plan, protected references, recovery evidence and backup-policy accounting.
Unknown retention policy preserves originals and blocks destructive application.
Mixed-source derivatives retain the highest contributing sensitivity; compression
never supplies declassification or factual authority. These are proposed owning
requirements, not a claimed implemented retention engine or accepted ADR.

## Refresh and next action

Keep this ledger synchronized at each checkpoint with the actual branch/PR,
commits, commands/results, remaining acceptance and exact next action. Refresh
open issue/PR state before selecting another batch. Use `Refs #…` for partial
work and leave new work in draft PRs; do not silently close umbrella scope.

B0 [#65](https://github.com/egohygiene/mindgarden/pull/65) and B1
[#66](https://github.com/egohygiene/mindgarden/pull/66) are merged. B1 functional
commit is `015f39676387a4e00c338fdb017a98c6cd11b821`; the final reviewed tree is
on main `44cc1e8`. B2 draft [#67](https://github.com/egohygiene/mindgarden/pull/67)
implements the bounded #30 lifecycle and named-view proof. Review its supported
Linux checkpoint; refresh live contracts before selecting B3 publication/portal
work or independent #27 release preparation. Retain native/restricted and policy
gates, real-consumer setup boundaries and all remaining parent acceptance.

### B1 implementation checkpoint

[Draft #66](https://github.com/egohygiene/mindgarden/pull/66), branch
`feature/16-local-federation-projections`, depends on B0 draft #65 at `3caea8d`. It adds the
[public discovery contract and reproducer](federation.md), proposed ADR-0011,
20 focused federation tests and committed synthetic golden artifacts/report.
The CLI proof combines two gardens and six public records, follows a catalog
reference into scoped search and a 5,691-byte context within 16,384 bytes, and
preserves references after export relocation and a clean rebuild. All network/
process entry points are blocked in-process; Google/model integrations are unused.
This is implemented on a review branch, not merged or fully accepted.

A public-output fix also excludes review-required/never-exportable contributions
before body reads and public revision calculation. Canonical files remain unchanged;
exports are create-or-verify and conflicting/incomplete directories are refused.
Incoming unsigned descriptors remain untrusted assertions. Full #16 consumer,
private-federation, incremental and authentication acceptance remains open.

Verification at functional `015f396`: 159 tests pass without skips on each of
Python 3.12.14 and 3.13.5. Fresh source/wheel, clean installed v0 smoke, both
compilation checks, Node 24.19.0, five proposed ADRs against pinned Hygiene,
pinned Aether continuity and whitespace checks pass. Clean -S source and isolated
-I wheel reproduce the federation report exactly; the clean-source private proof
also matches its original report. Main Test run 41960090464 and B0 run
41963994340 succeeded. B1 Test run 41965122996 also succeeded on `9149b2f`,
containing functional `015f396`; later documentation-only heads may have fresh checks.
No workflow was manually dispatched. Exact proof commands: [federation evidence](federation.md).

## Registry checkpoint after the B0/B1 merge

#65 merged at `38c4edf5740f0b05e279f3b1e3b98488d6f6ac4e`; #66 at
`44cc1e876282928685b5f3dba83d413db37b83c0`, with the tested `5f39fc2` tree.
Their earlier draft descriptions above are historical evidence. B2 (#30) now
proceeds on draft [#67](https://github.com/egohygiene/mindgarden/pull/67), branch
`feature/30-local-registry`, using synthetic gardens only. Initial lifecycle
commit `a47797b3d4ecb28052f42811eaa828f7868363ce` opened the draft. Named sessions
now check view membership/generation before root probes, and synthetic private
union/backlink fixtures preserve byte-identical public output. The ordinary-CLI
proof records exact evidence, bounded context, non-destructive unregister and
restore without reviving sessions. Dedicated directories keep history/staging
disjoint from canonical roots, including recognized unregistered gardens.
Repeated apply verifies the desired state.
Final functional `656f6b6fd19cbd1b03a0ee2c367f1bdfb79f0daa` passes 188 tests without
skips on each supported Python version. Fresh source/wheel, clean source and
isolated installed registry/private-workflow proofs, installed v0 compatibility,
compile/Node/whitespace and pinned owner/38-row coverage checks pass. Exact
commands/results: [registry evidence](local-registry.md). Initial lifecycle
automatic Test run 42107523013 passed; later head results are observed separately.
Full restricted/native-platform/cache-cleanup/organization-runtime acceptance
remains open. See [the registry contract](local-registry.md) and CONTINUITY.md.

## Source-workflow sprint checkpoint

Merged PRs #74–#79 complete the six bounded follow-ups in the
[source-workflow map](source-workflow-sprint.md). The combined checkout is
`feature/16-rendered-garden-references`; functional `b88cc97` passes 260 tests on
both supported Pythons, clean-source/isolated-wheel golden proofs and automatic CI.
The map records exact commits, stack bases, commands, failed-run corrections,
remaining parent criteria and the next review action. No parent was closed and
ADR-0007–0022 remain proposed/null approval.

## Private policy and storage continuation

The maintainer authorized #29 → #31 → #30 → #35 → #45 on top of merged #79.
The [checkpoint/dependency map](private-storage-sprint.md) records shared policy
decisions and the external Hygiene/Realm gaps before runtime coupling. No existing
draft is merged or parent closed by this continuation.

The private-storage continuation merged #80–#84
on top of #79. [Its evidence](private-storage-sprint.md) records exact sources,
commands, remaining owner gates and the combined checkout. #20 gains bounded
archive/PDF/media evidence without broader publication or consumer acceptance.
All 38 parent issues remain open; no proposed ADR is self-ratified.

## Authorized source/storage merge update — 2026-11-06

[PRs #74–#84 merged in dependency order](merged-pipeline-storage-checkpoints.md),
with the complete tested tree preserved. All 38 parent issues remain open. The
current merged evidence supersedes earlier draft-state observations in this
ledger without satisfying their remaining parent or cross-repository criteria.
Next: refresh this ledger for the maintainer's next issue group.
