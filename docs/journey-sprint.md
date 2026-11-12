# Reading and evidence journey — 2026-11-12

The maintainer authorized six bounded checkpoints in small draft PRs. Main is
`7594921fb89097d9dae04f14e3ebc967055aa470`. Existing privacy/storage drafts
#127 → #128 → #129 → #130 remain unchanged and unmerged; this sprint stacks on
#130 (`f92d4160fff63e70c21ca46a2bdabdd6a66ea8a5`). The combined checkout always
uses the last branch in the table. No issue closure, ADR acceptance, release,
private-data ingestion or deployment is implied.

## Dependency reconciliation and bounded scope

| Order | Issue | Checkpoint | Branch / base | Verification / next action |
| --- | --- | --- | --- | --- |
| 1 | #15 | Binary diagram and source caption selection, scratch catalog, immutable full original | [#131](https://github.com/egohygiene/mindgarden/pull/131), `feature/15-selective-diagram-journey` / #130 | 21 focused tests on each Python; next #13 |
| 2 | #13 | Mixed text/attachment authored curation, attribution and reviewed destination handoff | `test/13-mixed-media-curation` / #131 | Implementation preserved; local tests blocked by unavailable environment |
| 3 | #14 | Independently reviewed private incoming-reference repair and recovery | Next / #13 draft | Existing incoming inventory is a prerequisite; never auto-retarget |
| 4 | #16 | Explicit public bundle discovery to bounded cited context | Next / #14 draft | Existing descriptor/catalog/session contracts; no remote acquisition |
| 5 | #17 | Actual Quartz note, backlinks and provenance reading journey | Next / #16 draft | Reuse the pinned renderer and existing accessibility checks |
| 6 | #20 | Composed clean-checkout journey, migration/restore and exact rebuild | Next / #17 draft | Reuse all checkpoints; model and Google services disabled |

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

Next: bind the diagram, caption and scratch disposition
into an authored curation proof using exact independent evidence selectors.

## #13 interrupted mixed-media checkpoint

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
