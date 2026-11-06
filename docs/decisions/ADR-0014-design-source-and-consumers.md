---
schema: egohygiene.architecture-decision/v1
id: ADR-0014
title: Keep stack-neutral design tokens separate from derived consumers
status: proposed
date: "2026-11-05"
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/38
pull_request: null
related:
- ADR-0013
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/38
  description: Existing public visual references and portable design-source requirements.
exceptions: []
approval: null
---

# ADR-0014: Keep stack-neutral design tokens separate from derived consumers

## Context

The public banner and architecture illustration establish a botanical visual
direction. The first v1 preview needs a usable theme without choosing the future
application framework or requiring image generation for engine contributors.

## Decision

Propose versioned, validated JSON as the public design source. Keep semantic
colors, local font fallbacks, numeric dimensions and visual/prompt references
independent of Garden knowledge. Derive CSS and optional Quartz settings from
that source. Bind a selected theme revision into the existing site plan.

## Alternatives considered and rejected

Duplicated CSS/Quartz palettes drift independently. A framework-specific token
format would choose a product stack prematurely. Hosted fonts or mandatory image
generation add unnecessary network/service requirements.

## Consequences and tradeoffs

The small schema covers the current consumer, not a complete component library.
Contrast checks substantiate color pairs; they do not establish full WCAG
conformance. Native, slide and future web consumers remain separate adapters.

## Implementation and evidence links

[Design source and exports](../../design/README.md) and the
[batch checkpoint](../garden-experience-milestone.md) record checks and limits.

## Replacement or exit strategy

Replace or remove a consumer without changing canonical Garden records. Version
the design contract when incompatible token semantics are introduced.

## Follow-up work

Obtain human disposition independently of implementation. Complete application
component and accessibility evidence when the owning interface is selected.
