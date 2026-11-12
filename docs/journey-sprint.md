# Reading and evidence journey — 2026-11-12

The maintainer authorized the six checkpoints, then explicitly authorized merging
existing work and deferring broader local CI/`act` testing. PRs #127–#132 are now
merged in dependency order. Main is `f5baa3dac3f7624bea94f5224e136de6ef5482b0`;
its tree exactly equals the combined #132 head `0a675fde19dd746f4af98bf946521a93b247a3be`.
All six original PR heads have passing automatic Test/preparation CI. Execution
recovered; original uncommitted WIP is untouched and new work uses a clean
worktree. The current table and continued checkpoints supersede historical outage
observations below. Parent acceptance, private pilots, ADR ratification and
publication/release remain separate.

## Authorized merge receipt

| PR | Merge commit |
| --- | --- |
| #127 | `904809083a06a3bcb7f514122cbfb5ec53a4c900` |
| #128 | `e849d30f4e88f4089358128a3182d2a82ee4a6e3` |
| #129 | `4b547abdb73d9572596e8c9b2da3e72ec9a5334d` |
| #130 | `80a2e16dc6ac452db1b82eb55ff74725b315b538` |
| #131 | `ae8f438082997cdbe95d3c281323e89b5373f639` |
| #132 | `f5baa3dac3f7624bea94f5224e136de6ef5482b0` |

#132 Test **43278711469** and preparation **43278711575** completed successfully
on corrected head `0a675fd`. Post-recovery focused mixed-curation/diagram command
`python -m unittest tests.test_mixed_curation tests.test_archive_diagrams --quiet`
also passes **6 tests, zero skips**, Python 3.12.14 (4.062s). Hosted checks and local
checks are distinct evidence. No workflows were manually dispatched.

## Dependency reconciliation and bounded scope

| Order | Issue | Checkpoint | Branch / base | Verification / next action |
| --- | --- | --- | --- | --- |
| 1 | #15 | Binary diagram and source caption selection, scratch catalog, immutable full original | [#131](https://github.com/egohygiene/mindgarden/pull/131), `feature/15-selective-diagram-journey` / #130 | Merged; 21 focused tests each, hosted CI passes |
| 2 | #13 | Mixed text/attachment authored curation, attribution and reviewed destination handoff | [#132](https://github.com/egohygiene/mindgarden/pull/132), `test/13-mixed-media-curation` / #131 | Merged; corrected hosted CI and post-recovery local checks pass |
| 3 | #14 | Independently reviewed private incoming-reference repair and recovery | [#133](https://github.com/egohygiene/mindgarden/pull/133), `feature/14-reviewed-reference-repair` / main | Focused checks pass; draft for review |
| 4 | #16 | Explicit public bundle discovery to bounded cited context | [#134](https://github.com/egohygiene/mindgarden/pull/134), `feature/16-public-bundle-context` / #133 | Focused public-reader/schema/scope checks pass; draft for review |
| 5 | #17 | Actual Quartz note, backlinks and provenance reading journey | [#135](https://github.com/egohygiene/mindgarden/pull/135), `test/17-rendered-reading-journey` / #134 | Actual selected reading and focused checks pass; manual a11y items remain |
| 6 | #20 | Composed clean-checkout journey, migration/restore and exact rebuild | `test/20-composed-reading-recovery` / #135 | Source golden and 22 focused cases pass; qualify clean artifacts |

These are review-stack dependencies, not new blanket issue gates. #15 and #13
already have working source/curation contracts; this adds their missing mixed
media proof. Matching-scope private reference repair can proceed independently
of unavailable public declassification contracts. Public local bundle consumption
does not require private federation, signatures, a registry service or a package
installer. Existing #17 static rendering can be tested without a private web app.
The final composition depends on the new behavior, not real pilot authorization.

## #15 selective diagram checkpoint

Reread the supplied authoritative v2.0.2 specification sections 8.2–8.3. The
supported preservation schema explicitly represents image blocks by asset ID
and separate text blocks; it does not define an inferred image-caption field.
The synthetic fixture therefore retains the observed caption as message text
and its image relationship as `asset_id` / `source_refs`. No vision or invented
description is needed. Tests cover the existing v2.0.0, v2.0.1 and v2.0.2 source
profiles; full producer conformance remains unclaimed.

The blue three-box diagram and red scratch alternative are synthetic PNGs.
Selecting `asset-diagram` normalizes its exact bytes and both message text
locators. The scratch image is catalog-only; the complete immutable ZIP still
contains both images. Selection is not deletion, redaction or publication review.
Both images are checked even when unselected. Repeat/overlapping fallback exports
reuse unchanged evidence; changed captured input invalidates application before
writes. Transcript instructions remain untrusted data.

Exact focused command, using each supported interpreter:

```sh
python -m unittest tests.test_archive_diagrams tests.test_archive_v2 tests.test_archive_selection tests.test_conversation_archives
```

Python 3.12.14: **21 pass, zero skips**, 7.579s. Python 3.13.5: **21 pass, zero skips**, 7.714s. New-head CI remains unobserved;
it is not inferred from prior CI.

## Remaining parent scope and handoff

Collections/multipart and untested archive variants, broader curation/media and
public transitions, remote acquisition/authentication, manual WCAG/screen-reader
acceptance, the approved real private pilot and Empathy hosting/publication remain
open in their owning issues. Hygiene/Realm policy and confidential-runtime gates
are unchanged. All 24 ADRs remain proposed with null approval. #19/#27 and the
deferred #86–#91 cohort remain parked.

Draft #131 functional commit: `5a8a2b52bd9efed8ca58a0f21ce702e07d2a0105`.

Next: qualify the recovered mixed-media draft #132 when execution is available,
then continue with #14. Both drafts remain for review.

## Historical #13 interruption and recovery

The authored recipe binds five dispositions to exact normalized evidence: diagram
reference, corrected prompt summary, quotation, unanswered question and scratch
exclusion. Source messages distinguish the assistant proposal, later user
correction and quoted third-party assertion. The correction's synthetic account
label is omitted from the summary with an explicit evidence-bound redaction.
The question remains unreviewed. A separate reviewed private move places the
diagram in a project garden while the prompt stays personal, without copying the
raw archive or changing vault objects.

This is implementation preserved for review, **not passing verification**.
The managed execution environment became unavailable during preparation.
The original local test command did not start; its disconnected terminal session
cannot establish success. The text files were recovered through the GitHub
integration. Automatic PR CI, if observed, will be recorded separately from
required local checks. No new runtime behavior is claimed by this test checkpoint.

Exact resume action, from a usable clean checkout of this branch:

```sh
python -m unittest tests.test_mixed_curation tests.test_curation tests.test_curation_transformations tests.test_archive_diagrams tests.test_routing_lifecycle
python -m ruff check --select E9,F tests/journey_fixture.py tests/test_mixed_curation.py
python -m ruff format --check tests/journey_fixture.py tests/test_mixed_curation.py
```

Run the tests on Python 3.12 and 3.13, correct failures, update this receipt and
CONTINUITY, then proceed to independently reviewed incoming-reference repair
(#14). The broader #13 multi-target proposal protocol and model evaluation remain
open; this uses existing reviewed private transitions as the destination handoff.

## Recovery receipt and exact next action

Draft #131 head `0beaaefa56d6c29ea9606909eda2b50ace3ff2f8` is the tested
archive checkpoint plus its documentation handoff. Draft #132 functional head
`ff8be248d466a6180843727938454fc8d23e7fa1` preserves the interrupted curation
work. Both are unmerged and unreviewed. Later documentation commits do not imply
new software verification.

Automatic CI observed at 2026-11-12 18:15:00 UTC: #131 Test **43275891608** and #132 Test
**43277105896** have passing macOS 3.12/3.13 jobs, with both full Linux Python
jobs still running. Release-preparation runs **43275891128** and **43277105888**
pass. Full Test runs are **pending**, not passing evidence. No workflows were
manually dispatched. Required #13 local checks remain unavailable.

The managed execution environment reported unavailable, and exec rejected new
commands with “No usable execution environment is available.” Runtime status
metadata separately reported running; that observation did not restore command
execution. Existing local uncommitted files may differ from the recovered remote
branch. Preserve them; do not reset or clean the original workspace. When usable
execution returns, fetch and create a separate checkout:

```sh
git fetch origin
git worktree add --detach .cache/journey-resume origin/test/13-mixed-media-curation
```

From that checkout, run the #13 commands above with both interpreters and inspect
the exact functional-head CI logs. Fix any failures and record actual results
before extending the stack. No further user approval is needed for the already
authorized six checkpoints.

### Implementation resumption notes

- **#14:** extend the existing incoming inventory with a separately reviewed,
  exact-edge/target operation. Preserve the old edge and its intent; explicitly
  model how projections select the reviewed replacement. Reuse group transaction
  rollback/recovery and fingerprint checks. Include changed edges, targets,
  evidence, unsupported policy transitions and partial-failure retry cases.
- **#16:** consume only explicitly supplied, checksum/revision-verified public
  bundles through the descriptor/catalog boundary. Existing private local read
  handlers already work; avoid duplicating them. Enforce live output budgets and
  exact represented citations without treating producer assertions as authority.
- **#17:** extend `scripts/site_browser_check.py` on the already pinned Quartz
  renderer with note-page search, backlinks, exact provenance, keyboard/mobile
  and long-citation checks. Reuse prepared offline npm/axe caches. Full manual
  WCAG, private app and hosting acceptance remain separate.
- **#20:** compose the selected image/caption review, prompt retrieval, bounded
  context and new routing/discovery with existing vault migration and restore
  services. Run a fresh standalone proof and isolated wheel/source proofs with
  networking, Google and model calls blocked; compare exact source/index/graph/
  context identities after rebuild. Never substitute earlier partial goldens
  for this new composition or claim the real private pilot is complete.

At the outage, the next four rows were unimplemented. Current checkpoints above
and below supersede that observation. These notes are
implementation guidance, not accepted new architecture or completed acceptance.

### Corrected preliminary assertions

The superseded #132 functional Test run **43277105896** was cancelled by the
following documentation push. Its retained logs show two failed new assertions
on both Python jobs and the reviewed-destination case passing. This is failure
evidence, not a passing suite. Source review identified the two test assumptions:
the curation schema rejects an agent review authority as `CURATION_INVALID`
before the human-review guard; the index deterministically orders citations
independently of authored proposal order.

The corrected tests separately require agent-schema rejection and
`REVIEW_AUTHORITY` when human authority is absent, and compare complete exact
citation sets without imposing proposal order. The context assertion also checks
the 8192-byte bound. These corrections still require local and full CI
qualification; no product rule was weakened. Inspect the current PR head for the
corrected revision. Later superseded runs and pending current-head CI are not
passing evidence.

## Continued #14 reviewed incoming-reference repair

The versioned `reference-repair` request and event extend the existing garden,
provenance, relationship and recoverable group-transaction contracts. New CLI:

```sh
mindgarden route --local-config bindings.json --reference-repair repair.json --plan
mindgarden route --local-config bindings.json --reference-repair repair.json --apply --plan-digest SHA256
```

Each selected edge names exact original/source/historical-target/current-successor
revisions, a new replacement ID and rationale. Explicit human approval is required.
Only matching ordinary personal policies are supported. The replacement preserves
relationship type/direction, evidence, authors and qualifications. Originals and
source-owner bytes stay unchanged. A new provenance review and exact canonical
transition lineage enter the authorized evidence closure; missing or denied review
cannot leave a visible replacement. Historical repair stays valid if its successor
moves later; another explicit repair is required to follow that later move.

Conflicting repairs, duplicate selections, missing/unpinned evidence, changed
requests, inputs or policy fail closed. Two-owner cutover failure restores both
gardens; the same plan can retry. Normal CLI and owner validation verify the
append-only review, and session revisions bind the event before graph/backlink
retrieval. No automatic relationship reinterpretation or public transition is added.

Focused commands:

```sh
python -m unittest tests.test_reference_repairs tests.test_routing_incoming tests.test_routing_transfers tests.test_routing_lifecycle tests.test_mixed_curation tests.test_v1_contracts --quiet
python -m ruff check --select E9,F src/mindgarden/domain/reference_repairs.py src/mindgarden/domain/garden.py src/mindgarden/application/reference_repairs.py src/mindgarden/application/routing.py src/mindgarden/application/query_view.py src/mindgarden/interfaces/cli.py tests/test_reference_repairs.py tests/test_v1_contracts.py
```

Python 3.12.14: **37 pass, zero skips**, 30.500s. Python 3.13.5: the unchanged
35-case selection passed (28.319s), then both added cases passed (2.669s).
Ruff/new-file formatting pass. The initial 15-case run exposed missing transition
lineage in the authorized closure and two test setup/diagnostic assumptions;
those were corrected before this passing qualification. Full discovery and `act`
are intentionally deferred per the maintainer; `act` is not installed and Docker
is present. New draft-head CI is not yet observed.

Next: open the bounded #14 draft, then implement explicit public-bundle discovery
to lexical selection and bounded cited context (#16). Parent #14 still owns public/
policy-changing routes, unpinned-reference review and wider recovery acceptance.

Draft #133 functional commit: `b5a61f3d144fe854a83f45b26efe1057f6fbd059`.

## Continued #16 supplied public-bundle context

`federation query` consumes a versioned private request containing an existing
public catalog, selected bundle directories/expected revisions, query and byte/item
limits. It narrows the existing live session to already-authorized garden IDs.
A catalog cannot grant access, register gardens or supply tool capabilities.
Descriptor identity, digest and revision are checked before opening the selected
index; complete bundle verification precedes record filtering and lexical ranking.
Current metadata approval, public/publishable sensitivity, represented revisions,
retirement and claim-subject boundaries are enforced before counts and ranking.

The reader returns versioned JSON or bounded Markdown with original public
records, canonical routes, exact logical source references, represented public
revisions, qualification/review assertions and lexical score contributions. It
opens no canonical content bodies, fetches no network data, writes no records and
emits no local paths/session IDs. Expiry, revocation (including during a read),
output/candidate budgets and changed inputs fail closed. Publisher assertions stay
untrusted; checksums establish integrity rather than authenticity or truth.

```sh
mindgarden federation catalog --input supplied-bundles.json
mindgarden federation query --local-config bindings.json --scope public-session.json --input public-context-request.json --format json
mindgarden federation query --local-config bindings.json --scope public-session.json --input public-context-request.json --format markdown
```

The request contract and synthetic valid fixture show the exact fields. This
baseline reads ordinary federation-bundle directories for gardens already in the
session's authority. It is not a third-party package installer or remote/private
federation protocol. Unselected unavailable directories are not opened. Rendered
site package extraction, remote authentication/signatures and real Aether/Akashic
consumer adoption retain their owning scope; producer capabilities are unchanged.

Verification: Python 3.12.14 public-reader/federation/schema selection **32 pass**
(51.791s), plus the added mid-read revocation case **1 pass** (1.619s). Python
3.13.5 selection including scoped retrieval **47 pass** (61.794s), plus the same
added case **1 pass** (1.407s). Separate 3.12 scoped/local discovery regression
checks **23 pass** (24.845s). All have zero skips. Initial new-reader tests exposed
a too-narrow score-contribution schema and a wrong expected corruption diagnostic;
both were corrected before qualification. An exploratory routing/local invocation
also named nonexistent `tests.test_query_views` and failed; the explicit valid
scope/local commands above supersede it. No failed command is passing evidence.
Ruff/new-file format, owner/continuity/coverage and diff checks pass. Broader full/
`act` testing remains deferred; draft-head hosted CI awaits observation.

Next: open this draft on #133, then test actual note/backlink/provenance reading
on the pinned Quartz renderer (#17), followed by the composed recovery proof.

Draft #134 functional commit: `8012a10a54b2ebfdb9c60f9ebbea67d5765a75d0`.

## Continued #17 actual reading checkpoint

The actual pinned Quartz reader now has a keyboard search → selected note →
typed link → backlink journey. Both note pages compare rendered source locators,
content hashes, represented records and qualifications to the verified served
index. A committed synthetic long source identity exercises mobile citation
wrapping. The owned adapter normalizes native full-slug links/GET reads to static
folder routes, preserves query/fragment boundaries and external links, synchronizes
the localized theme action label after navigation, repairs table-of-contents
control targets and gives all contents links sufficient contrast. Native theme
behavior and logical note identities remain owned by their existing contracts.

[Actual Chromium evidence](evidence/journey-reading-browser.json): prepared pinned
renderer `075afd3f712da0088a07f5284a7b3aba37dd61b6`, offline npm cache,
Chromium 151 / Playwright 1.62.0 / axe 4.10.3, 320px and 1280px, light/dark and
200% text. The selected three-note garden renders twice to identical bytes; 60
artifacts verify. Keyboard reading, exact evidence, Request-based preview reads,
no-JavaScript note/backlink navigation, unavailable graph and portal preservation
pass. **13 axe audits report zero violations. Eight note audits still have manual
`color-contrast`/`duplicate-id-aria` review items.** They are not passing manual
WCAG evidence. Auxiliary Quartz routes, broader page variants, screen-reader and
real hosting/consumer acceptance remain open in #17.

```sh
python scripts/site_browser_check.py --workspace /tmp/mindgarden-note-reading-v4 --renderer /workspace/mindgarden/.cache/six-quartz --npm-cache /workspace/mindgarden/.cache/six-npm --axe-script /workspace/mindgarden/.cache/next-sprint/axe/node_modules/axe-core/axe.min.js --variant small --report /workspace/mindgarden/.cache/journey-sprint/17-reading-v4.json
python -m unittest tests.test_site tests.test_rendered_federation tests.test_design tests.test_portal --quiet
node --check profiles/quartz/v1.graph.js
```

The first command is the actual bounded run. It uses only prepared software and
loopback browser traffic; its paths are local execution controls, not portable
garden records. Omit `--variant` for the historical empty/small/large matrix; this
checkpoint reruns the changed small reading slice rather than claiming new empty/
205-note evidence. Focused tests: **30 pass, zero skips** on Python 3.12.14
(85.893s) and 3.13.5 (81.976s). Ruff, Node syntax and format checks pass. Static
site/reference/portal goldens were rebuilt: only owned layout revision, package/
catalog fingerprints and portal manifest changed; citations stay unchanged.

Earlier browser attempts exposed the static route and native action/ToC issues;
they also corrected an overly narrow URL glob and an initial interaction timing
assumption. The first post-asset 29-case regression selection had one stale portal
golden and is not passing evidence. Superseded Ruff unused-import findings were
removed. The final command and evidence above supersede those attempts; full
combined discovery and `act` remain deferred per the maintainer.

Next: open the #17 draft above #134, then finish the single no-provider archive/
review/search/context/private-reference/migration/restore/clean-rebuild proof (#20).

Draft #135 functional commit: `3b794ddbc28f18f52187effec4101c672cec7586`.

## Continued #20 composed offline proof

[The committed synthetic golden](../tests/fixtures/conversation-archives/reading-journey-proof.json)
and `scripts/reading_journey_demo.py` compose the supported checkpoints through
normal initialization, validation, review, routing, retrieval and vault commands.
A tested v2.0.2 source-profile archive contains a selected binary diagram/caption
and a scratch image. Repeat/overlap imports reuse unchanged normalized evidence;
a changed input invalidates application before writes. Authored review preserves
assistant attribution, the later user correction, quotation, unanswered question
and redaction rationale. Only the reviewed prompt enters the private context.

The prompt's exact normalized citation resolves to `CONVERSATION.json`
`/messages/1`, speaker assistant; source review remains **unreviewed**, knowledge
review is **approved**, and the mixed-attribution knowledge stays epistemically
**proposed**. JSON is **4,539 bytes** and Markdown **4,664 bytes**, each within
**8,192**. The diagram gets its reviewed private project home and an independent
incoming-reference repair. Eleven immutable vault objects, including both original
archives and the retained scratch original inside them, survive initialized vault
migration, explicit filesystem relocation, export and clean restore. The source
and former target vaults are retained. A cache-free clean garden reproduces the
exact index, graph, JSON/Markdown context and evidence response with changed
physical bindings and no paths in portable records.

A separate explicitly public synthetic slice proves catalog → supplied bundle →
bounded cited context (**5,192 bytes**) and matching static note routes. It does
not publish private knowledge or run a renderer; the actual renderer/browser
proof is separately linked above. Networking, HTTP and external process/model
entry points are blocked in the core proof; Google/model credentials are absent.
There is no mandatory database, model, Node or hosting dependency for this proof.

```sh
python scripts/reading_journey_demo.py --workspace /tmp/mindgarden-reading-journey-v3 --require-source --report /workspace/mindgarden/.cache/journey-sprint/20-journey-v3.json
python -m unittest tests.test_reading_journey tests.test_reference_repairs tests.test_public_bundle_context --quiet
```

Source proof passes. The focused composition/repair/public-reader selection passes
**22 tests, zero skips**, Python 3.12.14 (61.512s) and 3.13.5 (59.780s). Ruff and
new-file formatting pass. The first workflow attempt used the filesystem vault's
low-level initializer without its required reviewed plan; the corrected proof
uses the ordinary digest-bound `vault init` command and completes all steps.
That first attempt is not passing evidence. Clean wheel/unpacked-source artifact
qualification is the remaining independent verification at this checkpoint.

Hosted observations: #133 head `297c074` Test **43283297807**, preparation
**43283297519** and Decisions preview **43283298469** pass. #134 head
`81979b3` Test **43284993040** and preparation **43284993053** pass; Decisions
preview **43284993775** failed at generation with `RIW-004` / `ADR build:
acquisition: denied` while acquiring upstream inputs. This is an observed
external preview failure, not passing CI or a reason to weaken native ADR checks.
Local pinned owner validation passes. #135 head `38d2cd4` Test **43290873943**
was in progress and preparation **43290873617** passed when inspected. No workflow
was manually dispatched. Current-head checks must be refreshed before merging.

The real private archive/pilot, Empathy promotion/publication, untested archive
variants, remote integrations, manual a11y review and full parent acceptance stay
open. This checkpoint is evidence for #20, not closure of those responsibilities.
Next: qualify clean artifacts, open #136 on #135 and leave the complete new stack
for review; broader full discovery and local `act` can follow as authorized.
