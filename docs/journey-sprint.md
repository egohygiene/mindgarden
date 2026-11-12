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
| 1 | #15 | Binary diagram and source caption selection, scratch catalog, immutable full original | `feature/15-selective-diagram-journey` / #130 | 21 focused tests on each Python; open draft |
| 2 | #13 | Mixed text/attachment authored curation, attribution and reviewed destination handoff | Next / #15 draft | Reuse exact normalized evidence; do not require a model |
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

Next: open the first draft, then bind the diagram, caption and scratch disposition
into an authored curation proof using exact independent evidence selectors.
