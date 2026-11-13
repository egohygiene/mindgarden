# Remaining work and the local setup path

This is the 2026-11-13 sync after the authorized #144 → #147 stack. It is a
proposed finishing sequence, not acceptance of an ADR, permission to publish, or
permission to process unspecified private inputs. The
[coverage ledger](open-issue-coverage.md) retains every issue's full acceptance.

## What the open count means

There are **34 open issues**, with 44 tracked rows and ten closed. These are not
34 unbuilt features. The Python engine, CLI, private source vault, authored
curation, scoped retrieval, context, reviewed packet, optional Drive capture and
recovery already have implementation and synthetic acceptance evidence. The
[freshness/mapping proof](freshness-mapping-sprint.md) adds real context consumers,
multi-source refresh/live validity and reviewed CSV mapping. Live Drive/Codex,
the actual private pilot and the full product/public integrations remain distinct.

Every current open issue is assigned once below; the linked coverage rows give
its exact implementation and remaining evidence.

| Workstream | Open issues | Remaining purpose |
| --- | --- | --- |
| Local pipeline and consumer proof (11) | #13, #14, #15, #20, #35, #37, #45, #46, #87, #89, #90 | Finish specific compatibility/currentness gaps, actual model/provider tests and the explicitly approved consumer proofs; retain policy-dependent extensions |
| Policy and decision gates (4) | #29, #31, #41, #42 | Consume accepted information-flow/runtime contracts, review historical evidence and disposition architecture decisions; tests do not supply owner approval |
| Broader product and public integrations (8) | #16, #17, #18, #21, #43, #44, #47, #48 | Complete listed federation/rendering/portal/ADR/bookmark/infographic criteria and the actual shared API/private-app slice |
| Optional or deferred work (6) | #19, #27, #32, #34, #88, #91 | Query-store evidence and optional evaluation disposition; release and context-package/RDF work retain their explicit deferment |
| Umbrellas (5) | #1, #2, #5, #40, #86 | Reconcile child acceptance and close only when their own aggregate outcomes are met; they are not five separate implementations |

## Recommended finishing sequence

### 1. Close the actual acceptance gaps

Audit merged evidence against the issue text before writing another feature.
Mark criteria that are really met, record the precise remaining gate and close a
parent only when its listed requirements are proven. In particular, review
#15/#16/#32/#43/#44 for stale follow-up assumptions; this is an audit recommendation,
not a claim that those four are complete. Additional integrations are not silently
made prerequisites for a smaller already-specified outcome. Actual private-pilot
evidence is explicitly required by #37/#46; optional model adoption or larger
format support must not be added as automatic closure gates.

The earlier ledger treated richer bank formats, balances/assets, PDF/charts and a
real private pilot as #90 closure gates. Its acceptance explicitly specifies a
**synthetic** packet and excludes a live financial account or real consultation
from the fixture. Those broader features remain useful follow-ups under the
existing workflow/product owners, and the first clear remaining required #90 checkpoint is
correction/missing-evidence detection and stale-result handling. The acceptance
audit still verifies the other listed criteria before closure. No criterion is
removed or new implementation declared accepted by this correction.

### 2. Finish one small source-to-current-packet batch

| Proposed checkpoint | Existing owners | Concrete evidence |
| --- | --- | --- |
| Corrected or missing source → packet currentness | #37/#46/#90 | A synthetic source changes after a packet was reviewed. Its affected packet/summary is stale or review-required, an unrelated output stays current, and a new exact reviewed plan rebuilds without deleting the old evidence or silently approving changed facts |
| Selected Drive capture → reviewed CSV mapping → packet | #87/#90 | A fake provider supplies a file with one supported mapping. Preserve provider ID/revision, capture checksum, normalization config and exact row provenance through update, overlap, failure and restore. The local mapping proof alone is not this complete connector handoff |
| Archive acceptance audit and local extraction evaluation | #15/#13 | Verify the named-version, delivery, locator and selective-asset fixtures against the available authoritative contracts before adding compatibility work. Keep genuine unavailable-version gaps explicit. Run the separately required local-model extraction evaluation only with an explicitly selected available model, recording actual quality separately from wire mocks |

This continues existing contracts and does not require a database, a web app or a
hosted model. #14's broader public/policy-changing transitions and #35/#45's
confidential/provider extensions follow their actual owner contracts below.

### 3. Work the owner decisions in parallel

Live owner issues were refreshed at this sync. Hygiene #39 remains open without
the accepted classification/declassification specification. Realm #28/#29/#30
remain open for key-broker/vault/runtime assurance. These are real dependencies
for the corresponding #29/#31/#35/#45 and policy-changing #14 claims; an ordinary
filesystem or an `offline` flag cannot stand in for them.

Relay #5/#27/#33 and Pace #5 remain open for portions of the shared ADR adoption/
publication program. #41 must preserve historical authority evidence; #42 needs
human disposition of consequential proposals before selecting broader API/web,
auth, storage or runtime technology. All 24 current ADRs stay proposed/null
approval. Owner issue closure alone is not ADR ratification.

Akashic #173–#176 and Empathy #65 also remain open. Complete bookmark/public
handoffs and the golden consumer with those owners, without copying their policy,
catalog or deployment implementations into Mindgarden.

### 4. Prove consumers and the broader product

The user-selected local pilot can contribute evidence to #87/#89 and the explicit
private-pilot criteria in #37/#46. It is not, by itself, #20's approved legacy
conversation archive, Empathy integration and reviewed-public `/garden` proof.
Keep those acceptance outcomes separate.

Finish #16/#17/#18 public federation, accessible reading and portal composition;
then the actual #43/#44 Decisions consumers. #17 still needs its remaining manual
accessibility evidence. #47's shared CLI/API/web/worker slice follows the required
accepted decisions and runtime contract, with restart/recovery, keyboard/mobile
use and the listed cross-organization canaries. The private dashboard is #47;
the existing public Quartz/Obsidian-like site is #17.

Complete #48's independently reviewed public bookmark handoff and #21's renderer/
brand/candidate feedback under the existing publication boundaries. Nothing is
published automatically by merging engine work.

### 5. Disposition optional work and close umbrellas last

#32 is an optional query-store boundary, not a replacement canonical database.
Check its actual listed baseline/recovery/performance criteria before adding
incremental updates or treating permanent-store adoption as required.

#34's OpenViking trial records a real blocked native startup and unmeasured model
quality. The maintainer can choose a bounded remaining evaluation or an explicit
rejection/deferment; service adoption is not needed for the deterministic path.

#19/#27 release work stays parked pending organization release conventions.
#88 installable context packages and #91 RDF/JSON-LD/PROV evaluation remain the
deferred extension cohort. A literal zero-open backlog requires completing or
explicitly dispositioning deferred work, rather than calling parking completion.
Reconcile #1/#2/#5/#40/#86 after their actual child/aggregate criteria are met.

## The local setup track is already owned

No new setup issue is needed at this sync. #86 coordinates the selected local
workflow; #87 owns Drive binding/location/refresh, #89 owns the actual scoped
assistant integration, #90 owns the deterministic synthetic packet capability,
and #20 owns its separate archive/Empathy consumer proof. #47 already owns a
future private application and clean-start experience.

Use [the existing operator guide](private-pilot.md) and `pilot preflight`.
The first supported profile is explicit ordinary personal processing on owned,
untracked POSIX paths. Real classification and consumer/runtime authority must
fit that profile; restricted processing keeps its separate gate. Hosted assistant
access is separate from a local offline source grant.

| Setup stage | Existing owner | Completion evidence kept in the private consumer workspace |
| --- | --- | --- |
| Pick machine and locations | #86/#87 | Supported OS, separate software/control/garden/source-vault/output locations, actual classification and private permissions; credentials outside Git/portable records |
| Install and explore | #86 | Install an explicitly selected source/wheel without waiting for #19/PyPI; run the fictional garden and exact-reference/recovery commands |
| Connect a small collection | #87 | Locally configured OAuth and explicit folder/file selection, live capture/refresh and preserved provider identity; application selection is narrower than provider read-only OAuth consent |
| Import and review | #13/#15/#35/#90 | Exact captured originals, supported normalization/mapping, uncertainty and separate review of knowledge, reconciliation and packet selection |
| Use the actual assistant | #89 | Explicit permitted model/runtime, scoped Codex CLI/profile calls, exact citations, budget/revocation and model-disabled fallback; no implicit forwarding of private context |
| Prepare and recover | #86/#37/#46/#90 | Reviewed bounded packet, source corrections/staleness, gaps/questions and restore/rebind/rebuild with originals retained; no financial/legal conclusion inferred |

The operator-specific inputs still needed are the OS, chosen private locations,
first selected Drive collection and actual classification/runtime/assistant
permissions. OAuth credentials are configured locally, never pasted into chat.
No real source, account or credential is accessed by this sync.

The practical recommendation is to run this setup track alongside product
completion. The broader public site, package/RDF experiments and released 1.0
are independent of installing the current local engine. New issues should be
small concrete defects or missing capabilities found during that pilot, with
their own expected behavior; do not duplicate the existing setup owners now.
