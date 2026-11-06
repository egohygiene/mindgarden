# Six-checkpoint garden experience batch

The maintainer authorized six separate draft PRs: #17, #38, #10, #18, #42 and
#46. The base is merged main `8a9650e` (#67); its tree matches tested `3463d46`.
No PR in this batch is authorized for automatic merge. Use synthetic fixtures,
preserve the Python/v0 interfaces, and update this map and CONTINUITY.md at each
checkpoint. Real consumer gardens, archives and default registry configuration
are outside this batch.

| Issue | Bounded checkpoint | Required inputs and later proof |
| --- | --- | --- |
| #17 | Reviewed v1 records to an inspectable Quartz content projection, pinned local rendering and a loopback preview | Reuse #10/#12/#16 selection/scope contracts already on main. Establish the minimal immutable output manifest here; #18 extends portal composition. Full accessibility/large-graph/consumer acceptance remains separate. |
| #38 | Stack-neutral design tokens, schema, visual/prompt references and a validated Quartz/CSS consumer | Independent design source; integrate after the initial preview. It chooses no application framework. |
| #10 | Reusable adversarial publication/preview conformance and stable diagnostics | Extend the existing validator and new public output surfaces; retain v0 compatibility. Normative restricted-runtime assurance remains external. |
| #18 | Explicit caller-owned output, route/checksum manifest and isolated portal composition/recovery fixtures | Consume #17's artifact contract. Actual Relay/host deployment remains a separately pinned integration proof. |
| #42 | Focused proposed decisions, ownership/state map, deferred choices and executable follow-ups | Existing proposals remain proposed. Human disposition is recorded independently of implementation; no new application/store is implemented under this issue. |
| #46 | Versioned compaction/retention contracts, exact evidence and deterministic authored synthetic fixtures | Reuse #11/#13/#14/#15/#31/#45 contracts. Full approved private-pilot proof follows #20; destructive retention is unavailable. |

This is a review stack for a reproducible combined checkout. Stacking independent
documentation/style work does not make it a new semantic prerequisite. Accepted
architecture is still required for consequential later product choices.

## #17 reference behavior

V1 `publish project`, `publish verify`, `site build` and `site serve` use explicit
local bindings, an approved public site projection and a public publication
session. Existing v0 dispatch remains available. Site profiles extend the existing
`projection/v1` record with a typed `x-site` adapter declaration. Selection,
provenance, publication allowlists and represented revisions come from the same
application service as public federation; no parallel authorization model exists.

Content is rendered as literal reviewed text in this initial adapter, preserving
Markdown/HTML/instruction-bearing strings as data. Generated typed links and
exact citations supply navigation and provenance without opening original raw
archives. Rich body-Markdown and attachment rendering are explicitly outside this
first checkpoint. An empty selection produces a useful empty-garden page.

Projection planning and application need no Node service or network. Rendering
uses a separately prepared exact Quartz commit and offline npm cache. Dependencies
are installed in an owned temporary build tree with `npm ci --offline
--ignore-scripts`; the prepared renderer/source garden are read-only inputs.
Renderer setup is an optional acquisition integration, not a query operation.
The renderer's pinned package lock owns dependency integrity. Host process/network
isolation assurance remains a separate Realm/Hygiene contract.

Outputs are immutable create-or-verify trees. The manifest records public
represented revision, adapter pin, canonical note routes and every output hash.
Plans contain private control digests and are never-exportable. Changing profile,
selected knowledge, session, output or engine location invalidates the reviewed
plan. A conflicting or incomplete output is retained for inspection.

## State and recovery

Current branch: `feature/17-v1-garden-preview`; first draft pending. The 188-test
merged baseline passes. Targeted site/schema/v0-publishing checks pass; actual
rendering, browser checks and packaging evidence are being completed in the same
draft checkpoint. Later rows will record branch/PR, functional commits, exact
commands, CI separately from local checks, blockers and the next action.
