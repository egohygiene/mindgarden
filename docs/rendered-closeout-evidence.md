# Rendered garden, portal and public consumer checkpoint

Refs #17, #18, #20; this advances bounded checkpoints, not parent acceptance.
The operational review stack is #110 → #111 → the rendered closeout draft.
TypeSafe is independent of the public renderer; stacking preserves one combined
checkout rather than asserting a new semantic prerequisite.

## Superseding mobile navigation checkpoint — 2026-11-09

The [new receipt](evidence/overnight-rendered-browser-proof.json) supersedes the
mobile Explorer finding in the historical #112 report below. Owned adapter code
now assigns disclosure state and `aria-controls` to the native mobile/desktop
buttons and removes stale state from ordinary containers. The exact pinned
Explorer 0.1.0 controller uses the `collapsed` class; its vendor source is not
forked or patched. A bounded observer follows that class and cleans detached
panels on navigation. Button activation, layout and source ownership remain.

The actual Quartz commit and package lock stay pinned. The Explorer artifact is
`@quartz-community/explorer` 0.1.0, npm integrity
`sha512-qdsXF9ivT32ct52CzOLXCFnxHJS6xHIcX/lVeT82sEmNxjivRLt8kvVK+mJQBiC/Nj8ItRFiL+e0suwNZ19vjQ==`.
This records the existing evaluated integration; no new renderer/dependency is
selected. Source/portal proof goldens change only derived revision/manifest hashes
for the corrected owned script, not knowledge, source citations or stable routes.

All three actual empty/small/205-note builds pass. Keyboard Enter/Space opens and
closes mobile Explorer with synchronized native-button state and a valid controlled
content target. Expanded mobile navigation plus light/dark mobile/desktop views
produce **15 axe audits, zero violations and zero incomplete findings**. Skip
focus, search, graph links/controls, reduced motion, 200% text, no-JavaScript lists,
unavailable graph and actual portal interruption/retry proofs still pass. The
small renderer output reproduces byte-identically across two real builds.

Reproduction uses the complete prepared cache (the unrelated smaller cache
lacks `zwitch`; its first offline attempt failed and is not counted as passing):

```bash
python scripts/site_browser_check.py \
  --workspace /tmp/new-mindgarden-rendered-proof \
  --renderer .cache/six-quartz --npm-cache .cache/six-npm \
  --axe-script .cache/next-sprint/axe/node_modules/axe-core/axe.min.js \
  --chromium /usr/bin/chromium --report /tmp/new-rendered-browser-proof.json
```

Page requests remain loopback-only; scoped rendering uses offline npm and calls
no model or Google service. These are bounded automated/browser proofs, not a
full WCAG 2.2 AA or screen-reader certification, hosted publication or full #17
acceptance. Visual/manual/consumer qualification and the other parent gates
remain. The historical evidence is preserved below with its original limits.

## Actual pinned renderer and browser

[`scripts/site_browser_check.py`](../scripts/site_browser_check.py) creates only
synthetic public gardens, copies a prepared immutable Quartz checkout and npm
cache, and runs the actual offline renderer. It never acquires software during
scoped generation. The renderer remains
`075afd3f712da0088a07f5284a7b3aba37dd61b6`, Node 24.19.0.
Browser automation uses Playwright 1.62.0, Chromium 151.0.7922.173 and axe-core
4.10.3. These are optional verification tools, not engine dependencies.

The [full synthetic receipt](evidence/rendered-browser-portal-2026-11-08.json)
records output manifests, browser checks, actual rule findings and timings:

| Selection | Notes/claims | Rendered files | Build seconds | Browser graph ready, 320 / 1280 px |
| --- | --- | --- | --- | --- |
| Empty | 0 | 52 | 5.442 | 0.419 / 0.352 s |
| Small | 3 | 60 | 6.093 | 0.347 / 0.310 s |
| Larger | 205 | 262 | 125.323 | 0.329 / 0.260 s |

These are single local observations, not general performance guarantees. The
larger build cost remains a performance follow-up. The interactive graph has a
200-node ceiling; larger selections use the complete textual relationship list.
The small selection was actually rendered twice with identical complete bytes.
All three outputs exclude the synthetic unreviewed/private-control canaries and
machine-specific source paths.

Browser checks exercise keyboard activation of the skip link and zoom, graph
links into cited notes, search focus, light/dark theme controls, 320/1280-pixel
layouts, 200% text size, reduced motion, JavaScript-disabled relationship lists,
and unavailable-graph fallback. Page requests are restricted to the loopback
server; no model, Google or remote asset service participates. This is the
explicit `mindgarden-v1` theme checkpoint, not every possible consumer theme.

Corrections from actual output: owned graph controls are disabled until useful;
empty, oversized and failed graphs keep them disabled. Pinned pages gain a main
landmark and skip target without removing Quartz's article hooks. An owned click
handler keeps skip activation within the page despite SPA navigation. Theme
Explorer links use the opaque semantic accent; the previous blended link color
measured only 3.92:1 against its background.

**Historical #112 accessibility was partial.** Its mobile variants retained the pinned
Quartz Explorer's invalid `aria-expanded` attribute (`aria-allowed-attr`, critical).
It is recorded in every applicable axe result. Automated rules cover the garden home;
SVG contrast and broader graph reading still require manual review. No full WCAG 2.2 AA, screen-reader, all-theme
or real-consumer acceptance is claimed. That receipt did not suppress or reclassify the finding; the superseding
checkpoint above corrects native disclosure semantics and re-runs the audits.

Prepare optional tools independently, then reproduce with a new workspace:

```sh
python3 -m pip install playwright==1.62.0
npm install --prefix .cache/browser-tools --cache .cache/browser-npm \
  --save-exact --ignore-scripts --no-audit --no-fund axe-core@4.10.3
python3 scripts/site_browser_check.py --workspace /tmp/new-rendered-proof \
  --renderer /prepared/quartz --npm-cache /prepared/npm \
  --axe-script .cache/browser-tools/node_modules/axe-core/axe.min.js \
  --chromium /usr/bin/chromium --report /tmp/rendered-proof.json
```

Renderer preparation follows [the existing instructions](v1-site.md). A failed
attempt remains inspectable; use a fresh workspace. The executable asserts
software behavior and retains known external findings. Its receipt status is
`partial-renderer-accessibility-findings`, not a passing accessibility report.

## Actual artifact composition and recovery (#18)

The 60-file actual small Quartz artifact is pinned by represented revision and
manifest SHA-256, then composed using the existing portal service beside the
committed synthetic intelligence, decisions and history surfaces. An injected
receipt-write failure leaves complete inspectable garden bytes but no valid
composition receipt; verification fails. Retrying unchanged inputs creates the
receipt, repeat application verifies, and all sibling bytes remain unchanged.
A corrupted later candidate is rejected while the previous complete portal
still verifies. No deployment or promotion occurs.

Relay main `b4a88db20bc26f9ddefbee174baa8162cbe94ff2` and open
[Relay #40](https://github.com/egohygiene/relay/issues/40) were refreshed. The
tree contains no reusable Mindgarden action, so that integration cannot be
claimed. Full #18 retains pinned owner-action adoption, Empathy migration and
host promotion/rollback/publication acceptance. This local proof uses the
existing contract and does not copy or invent Relay orchestration.

## Empathy external-engine rehearsal (#20)

[Empathy draft #120](https://github.com/egohygiene/empathy/pull/120) now pins merged
Mindgarden `f3a88ccf7d67deb8ecf188d10d9cd496ed6a4973`. Its follow-up
`6d6630c89ee8e0db83d1434c2f52313001b485dc` records this non-destructive rehearsal.
A fresh VCS installation verifies PEP 610 commit identity and imports from its
interpreter prefix. Scratch inputs represent public consumer
`4e721715ec56a126f4efe2043298a34e6559335e`: committed garden, README, old entrypoint,
explicit publication profile and only the document/workflow evidence cited by
those notes. There is no incubated Python engine in the scratch copy.

With networking restricted during verification, version, five-note validation,
search, bounded JSON context, public projection and deterministic public verify
all return 0. Strict verification of the old entrypoint returns 3. Regenerating
`llms.txt` only in the scratch copy with the installed engine, then verifying,
returns 0. The working consumer's garden, tracked entrypoint, tasks and workflows
remain byte-identical. Its 12 existing consumer integration tests pass (0.040s).
The consumer PR documents the exact reproducible staging commands.

The required manual exact-head holistic MegaLinter check is not run: the
maintainer prohibited manually launching paid workflows. The draft does not
claim readiness. Canonical entrypoint acceptance, full-profile evidence, shared
Relay adoption and deployment remain open. The real private archive/pilot is
also unapproved; no private consumer or data was accessed.

The separate [installed first-pass compaction receipt](evidence/installed-source-compaction-2026-11-08.json)
proves that the new source/bundle contracts ship in a dependency-free wheel and
work through normal commands, with zero reviewed knowledge anchors and unchanged
originals. This complements the [complete synthetic journey](consumer-journey.md)
and relocation/rebuild evidence; it does not complete #20's broader acceptance.

## Subsequent selected-note reading checkpoint — 2026-11-12

The continued journey extends actual browser qualification beyond home/graph pages. Native static routes, theme action labels and table-of-contents controls/contrast were corrected after note-level findings. The [current reading receipt](evidence/journey-reading-browser.json) and [exact checkpoint](journey-sprint.md) record two viewports, two note pages, light/dark, keyboard links, exact source/record references and no-JavaScript reading. Thirteen axe audits have zero violations; eight note audits retain manual color-contrast/duplicate-id-aria items. This does not establish full manual WCAG, screen-reader or hosting acceptance. The earlier broad empty/205-note matrix remains historical evidence, not a rerun claim.
