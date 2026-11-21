# Synthetic journey and private-pilot checkpoint (#20)

`scripts/release_journey_demo.py` composes the current archive workflow with
reviewed routing, exact retrieval/context, local `/garden` content and public
federation. It uses only committed synthetic fixtures and existing application
services through the normal CLI. This checkpoint extends #64/#84. The owner
evidence and remaining integration checks are recorded below.

## What the synthetic journey proves

The archive produces an authored, explicitly reviewed prompt-bank entry. Search
and context retain its exact message/source revision. Export, restore, relocation
and a clean projection rebuild preserve that reference. A second authored
candidate demonstrates an explained private fallback and a duplicate-safe repeat.

A separate, already-public synthetic source is normalized and explicitly reviewed
before a selected procedure routes to the repository garden. That branch retains
its own exact public evidence and emits a 3,378-byte public context within a
16,384-byte budget, local `/garden` content routes and a verified federation
descriptor. Public bytes exclude private archive identities, candidate names,
paths and metadata. This is a public-reference composition, not automatic
declassification of private archive facts.

```bash
python3 -S scripts/release_journey_demo.py \
  --workspace .cache/release-journey --require-source \
  --report .cache/release-journey.json
cmp tests/fixtures/release-journey/expected-proof.json .cache/release-journey.json
```

Use a new or empty synthetic workspace. Network, external processes, Drive and
models are blocked or unused. The committed [golden](../tests/fixtures/release-journey/expected-proof.json)
distinguishes verified content projection from renderer execution and deployment.
Earlier mixed archive/PDF/media triage and recovery evidence remains in
[the storage sprint](private-storage-sprint.md); source and knowledge review
remain independent. An authored agent fixture is not claimed as a live model or
real-person approval.

## Private pilot: explicit inputs, private control and exact review

The pilot helper is separate from synthetic demos. It accepts a supplied archive,
an explicitly approved private workspace, source classification, capture time and
format version. It refuses this public repository and version-controlled output
locations, unsafe paths and unowned existing workspaces. Plans bind source bytes,
optional authored curation proposal, engine version, target fingerprint and expiry.
Changed inputs invalidate application. Replays verify the recorded result.

Restricted or unknown classification fails **before opening the source** because
verified confidential processing remains unavailable. A personal pilot requires
explicit operator classification; the helper never guesses or downgrades a source.
The actual archive/workspace/classification question is pending with the maintainer.
No real private archive has been processed by this checkpoint.

For an already approved personal source, use private paths and its actual supplied
capture timestamp. The following placeholders are operator inputs, not fixtures
or defaults to infer:

```bash
python3 scripts/private_pilot.py plan \
  --archive "/approved/private/archive.zip" \
  --workspace "/approved/private/new-pilot" \
  --classification personal --manifest-version "3.2.3" \
  --captured-at "<actual-supplied-ISO-8601-capture-time>" --owner "<approved-owner-id>" \
  --plan-file "/approved/private/control/normalization-plan.json"
```

Inspect that private plan. Apply its exact returned digest:

```bash
python3 scripts/private_pilot.py apply \
  --plan-file "/approved/private/control/normalization-plan.json" \
  --plan-digest "<reviewed-plan-sha256>"
```

The first normalization leaves source review unreviewed. Author and inspect a
curation proposal using the exact normalized evidence, then plan a continuation
with the same source/workspace/capture metadata and `--proposal` pointing to its
private file. Its supplied review authority is enforced by the existing curation
service. Without reviewed knowledge, the report explicitly remains partial.
The helper does not manufacture a reviewer, model output or attachment-selection
decision. All originals stay in the private vault; failed partial state is retained
for inspection and requires a fresh reviewed plan when its fingerprint changes.

Full context, control paths and receipts stay private. The allowlisted redacted
report contains no source path, filename, hash, text, identity or private count.
It is written inside the private workspace and remains private until the owner
approves sharing. There is no automatic commit, issue upload or publication.
Personal local operation is not a confidential-host assurance claim.

## Accepted Empathy consumer and remaining integration

The release ledger preserves the earlier optional consumer rehearsal. Empathy
subsequently accepted its golden consumer at
`f19fe1b072d3690b30b4314a92b41f8b5803459a`. The standalone engine indexes
18 root architecture documents and the generated repository context. That
context links to the Hygiene catalog at its immutable source revision.
The same acceptance covers OpenWiki and Obsidian
file-exchange prototypes and a reviewed-public Quartz site. All four jobs in
the exact-head publication run succeeded. Its native receipt bound six public
projection hashes and the live check rehashed 17 fixed routes. This evidence
supports the consumer, catalog/context reference and projection criteria in
#1, #2, #5 and #20. [Release ledger](release-checkpoints.md)
· [Empathy #65](https://github.com/egohygiene/empathy/issues/65)
· [Imported context](https://github.com/egohygiene/empathy/blob/f19fe1b072d3690b30b4314a92b41f8b5803459a/docs/ecosystem/CONTEXT.md)
· [Publication run 43643745065](https://github.com/egohygiene/empathy/actions/runs/43643745065)

The Quartz profile mounts the Garden at `/empathy/` beside `/empathy/intelligence/`.
On 2026-11-21, both routes returned HTTP 200 and `/empathy/garden/` returned
HTTP 404. #18 and #20 still need the dedicated `/garden` consumer mount and
the reusable Relay action. Relay #4 is closed. Relay #40 remains open, and its
inspected main tree `5de708368b42601e140c58f4ab8f305fe2dc5c82` has no Mindgarden
action. The local portal proof exercises sibling preservation and recovery
through the existing artifact contract. [Local portal proof](portal-composition.md)
· [Deployed Quartz profile](https://github.com/egohygiene/empathy/blob/f19fe1b072d3690b30b4314a92b41f8b5803459a/mindgarden/profiles/quartz/profile.yaml)
· [Relay #40](https://github.com/egohygiene/relay/issues/40)

#20 still needs the owner-approved real legacy archive, reviewed selection and
reconciliation, and a redacted conformance report. Closed #15 covers named
importer profiles and documents compatibility gaps for unavailable contracts.
Aether #51 remains open for the reusable curator skill and validated ChatGPT
handoff. The deployed consumer uses a pinned source commit. #19 and further
#27 release work remain deferred.
[Importer evidence](acceptance-reconciliation.md#15--importer-and-downstream-evidence-acceptance)
· [Aether #51](https://github.com/egohygiene/aether/issues/51)
