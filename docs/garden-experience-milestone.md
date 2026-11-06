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

| Issue | Branch/base | Draft | Functional checkpoint |
| --- | --- | --- | --- |
| #17 | `feature/17-v1-garden-preview` / main `8a9650e` | [#68](https://github.com/egohygiene/mindgarden/pull/68) | `f1706a55a41c0528489b503662f708e1b4884e31` |
| #38 | `feature/38-design-tokens` / #68 | [#69](https://github.com/egohygiene/mindgarden/pull/69) | `5b59d8e3c6b8b0fbdb1acdcf25a76ebf99968f18` |
| #10 | `feature/10-public-conformance` / #69 | [#70](https://github.com/egohygiene/mindgarden/pull/70) | `49e394a176436562e9eeab319829372127cd3961` |
| #18 | `feature/18-portal-composition` / #70 | [#71](https://github.com/egohygiene/mindgarden/pull/71) | `6df72c4cd18d23b0740d57e6ddd25b8e8f24172e` |
| #42 | `docs/42-architecture-decisions` / #71 | [#72](https://github.com/egohygiene/mindgarden/pull/72) | `d17f01c4cfa01145090d14aff97624f636fe7f92` |
| #46 | `feature/46-compaction-contracts` / #42 checkpoint | Pending | Contracts and authored synthetic proof |

#17 verification at `f1706a5`: 197 tests pass without skips on Python 3.12.14 and
3.13.5. Fresh source/wheel resources, both compile checks, Node 24.19.0, whitespace
and pinned Hygiene/Aether metadata checks pass. Clean `git archive` source with
`-S` and isolated installed wheel with `-I` both reproduce
`tests/fixtures/site/expected-proof.json` exactly. An actual offline Quartz build
produces 58 files/three canonical note routes; source and installed wheel render
byte-identical trees. Chromium verifies exact source hash/locator, canonical URL,
search (six public results), one selected backlink, three SVG nodes/one typed
edge and zoom. No external browser request or uncaught page error was observed.

Mobile overflow was observed and is an explicit #38 follow-up; full WCAG/large-
corpus/consumer acceptance remains open. The [automatic Test run](https://github.com/egohygiene/mindgarden/actions/runs/42150215705)
passed on `f1706a5`; later heads receive separate checks. No workflow was manually
launched. Exact CLI and optional preparation commands: [v1 preview](v1-site.md).


## #38 design checkpoint

The public `design/` source derives its botanical palette, thin linework and
spacing from the existing banner/architecture illustration. Versioned JSON,
strict schema and visual/image/diagram references remain independent of any web
framework. `mindgarden design --format json|css|quartz` validates and exports
without a network service. Optional `x-site.theme` selects the derived consumer;
the actual immutable token revision participates in the site plan.

All 201 tests pass on Python 3.12.14 and 3.13.5 without skips. Normal text/link
pairs meet 4.5:1 and focus/control pairs meet 3:1 on both surfaces/modes. Negative
fixtures reject unknown fields, font injection and insufficient contrast. Fresh
source/wheel packaging, both compile checks, owner metadata and whitespace pass.
An actual offline Quartz render produces 60 files. Chromium verifies search,
backlinks, three SVG nodes/one typed edge and zoom, with no horizontal overflow
after resizing from 1360px to 390px. Zero external requests or page errors were
observed. The isolated installed wheel exports the same validated tokens.
Responsive navigation is exercised; this remains a bounded color/layout check, not full WCAG acceptance.
Exact local checks:

```sh
.venv/bin/python -m unittest discover --start-directory tests --verbose
.cache/python313/bin/python -m unittest discover --start-directory tests --verbose
.venv/bin/python -m unittest tests.test_design tests.test_site --verbose
.venv/bin/python -m build --sdist --wheel
.venv/bin/python -m compileall -q src tests
.cache/python313/bin/python -m compileall -q src tests
python3 .cache/six_owner_checks.py
git diff --check
```

The owner check uses the pinned Hygiene/Aether schemas documented in the
[decision policy reference](decisions/policy-reference.json). ADR-0014 is proposed
with null approval. Full component/consumer/accessibility acceptance remains open.


## #10 publication/preview conformance checkpoint

The [reusable pack](publication-conformance.md) extends the existing validator,
v0 publication, scoped retrieval and exact-evidence suites with committed
adversarial surface canaries. It adds complete bounded output-tree inspection,
unique exact canonical routes, ordinary-file/link checks, per-request preview
integrity/authority and shareable JSON/human failures. The renderer's sibling
npm/log subtree cannot overlap declared vaults or canonical records. No denied
root is probed to establish that boundary.

The synthetic pack runs 80 tests without skips against source and an isolated
installed engine. The complete compatibility suite runs 210 tests on Python
3.12.14 and 3.13.5. Fresh source/wheel resources, both compile checks, pinned
owner metadata and whitespace are checked separately. Exact commands:

```sh
.venv/bin/python -m build --sdist --wheel --outdir .cache/dist
.venv/bin/python -m unittest discover --start-directory tests --verbose
.cache/python313/bin/python -m unittest discover --start-directory tests --verbose
.venv/bin/python scripts/publication_conformance.py --require-source --report proof-source.json
.cache/six10-wheel/bin/python -I scripts/publication_conformance.py --require-installed --report proof-wheel.json
```

Loopback HTTP is used only for synthetic preview checks. Rendering remains an
optional separately prepared adapter; mocked failure output contains synthetic
canaries so subprocess strings cannot leak through shareable diagnostics.
Consumer media coverage and normative policy/restricted-runtime assurance remain
open parent criteria. This is not source-rights or sensitivity adjudication.


## #18 local portal-composition checkpoint

[The local contract](portal-composition.md) extends #17's manifest with a private
request/plan and portable last-written ownership receipt. It requires both the
represented revision and exact rendered manifest SHA-256, complete site and
public-discovery validation, canonical base/mount agreement, and create-or-verify
output. Existing sibling surfaces and conflicts remain untouched. Receipt-write
failure leaves a complete copy that unchanged-plan retry can finish; incomplete
pre-existing trees are retained instead of silently repaired.

Eleven targeted fixtures cover schemas, project/subdomain/non-Pages bases,
changed inputs, symlinks, conflicts, exact pins, sibling preservation,
receipt failure/retry and relocated rebuilds. The complete suite runs 221 tests
on each supported Python version. The authored synthetic demo and isolated wheel
match `tests/fixtures/portal-composition-expected.json`; they do not invoke a
renderer. Separately, composing the actual pinned offline Quartz artifact
preserves 60 files/three note routes and all sibling bytes, with idempotent repeat.
That public receipt revision is
`sha256:30870e3b4bf0c401bfcd69cd82630f274d501213d64bf00a4e8abea4bfcb6305`.

```sh
.venv/bin/python -m unittest tests.test_portal --verbose
.venv/bin/python -m unittest discover --start-directory tests --verbose
.cache/python313/bin/python -m unittest discover --start-directory tests --verbose
.venv/bin/python -m build --sdist --wheel --outdir .cache/dist
python -S scripts/portal_demo.py --require-source --workspace new-proof --report proof.json
.cache/six18-wheel/bin/python -I scripts/portal_demo.py --require-installed --workspace new-wheel-proof --report wheel-proof.json
```

Both compile checks, fresh distribution resources, owner metadata and whitespace
also pass. The inspected Relay commit, unavailable Mindgarden action and exact
handoff requirements are pinned in the contract document. No deployment or
workflow dispatch occurs. Full #18 integration/production criteria remain open;
ADR-0015 remains proposed/null approval.


## #42 architecture proposal checkpoint

The [decision/ownership map](target-architecture.md) covers all ten issue topics.
Six new focused ADRs (0016–0021) address stores, user/tenancy boundary, runtime,
operations/retention, agent interfaces and integrations. Existing ownership/source/
service/scope proposals gain explicit migration costs and follow-up owners.
ARCHITECTURE.md, SYSTEM.md and ROADMAP.md distinguish implemented main, tested
drafts, proposals and deferred work. This branch changes documentation only.

The pinned Hygiene metadata/policy/decision-set/index checks and Aether continuity
checks pass; relative links and whitespace are checked. Runtime remains the exact
#71 implementation that passed 221 tests on both supported Python versions. No
redundant local full-suite run is claimed for this documentation-only checkpoint.
All new ADRs remain proposed/null approval. #40/#41, owner policy/contracts,
bookmark proof and human ratification remain open gates.
