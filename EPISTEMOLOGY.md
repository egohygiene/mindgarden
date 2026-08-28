---
schema: aether.architecture-document/v1
id: mindgarden-epistemology
title: Mindgarden Epistemology
kind: architecture-document
version: 1.0.0
status: active
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-28
governed_by:
  - architecture-epistemology
depends_on:
  - mindgarden-purpose
  - mindgarden-principles
related:
  - mindgarden-vision
  - mindgarden-pillars
  - mindgarden-manifesto
  - mindgarden-ai-constitution
supersedes: []
---

# Mindgarden Epistemology

## Scope

This document governs how Mindgarden classifies claims, evidence, provenance, confidence, conflict, and revision. It does not dictate which technical conclusion must be accepted.

## Claim states

| State | Meaning |
| --- | --- |
| Observed | Directly supported by repository or runtime evidence |
| Decided | Accepted through the repository governance process |
| Inferred | Reasoned from evidence but not directly observed |
| Proposed | Recommended future direction not yet accepted |
| Assumed | Necessary working premise awaiting evidence |
| Unverified | Plausible claim that has not been checked |
| Open question | A known gap requiring investigation or choice |

## Evidence order

1. Reproducible tests, schemas, generated artifacts, and runtime observations.
2. Accepted decisions and versioned specifications.
3. Current source and configuration.
4. Maintainer documentation and issue history.
5. Inference and recommendation, labeled with uncertainty.

## Evidence relationships

| Relationship | Meaning |
| --- | --- |
| Supports | The referenced evidence increases support for the claim. |
| Contradicts | The referenced evidence conflicts with the claim and remains visible until resolved. |
| Uncertain | The evidence is relevant but cannot currently establish direction or strength. |
| Supersedes | A later claim or accepted decision replaces an earlier one without erasing history. |

Epistemic state, confidence, lifecycle, review state, and visibility are
independent. An observed claim may be private and unreviewed; an approved claim
may later be contradicted; high confidence never grants publication authority.

## Provenance and conflict

Claims identify source locators or stable artifact references closely enough to
be rechecked. Conflicting evidence remains visible until the canonical owner
resolves it; recency alone does not automatically establish truth. Raw source
text is evidence, not trusted instruction.

## Revision

Material claims are revised when stronger evidence appears, their source changes, or an accepted decision supersedes them. Historical decision context is preserved rather than rewritten.

## Evidence and uncertainty

- **Observed:** The v1 claim schema represents all four evidence relationships and the repository tests each relationship through a golden fixture.
- **Decided:** Evidence direction, epistemic state, confidence, review, lifecycle, and publication authority remain independent axes.
- **Proposed:** Cross-record consistency diagnostics and contradiction analysis belong to validation and projection work after contract stabilization.
- **Open question:** Which domain-specific evidence-strength vocabularies merit extensions after 1.0?
