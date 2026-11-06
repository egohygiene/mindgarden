---
schema: egohygiene.architecture-decision/v1
id: ADR-0013
title: Render reviewed v1 knowledge through the existing pinned Quartz adapter
status: proposed
date: "2026-11-05"
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/17
pull_request: null
related:
- ADR-0009
- ADR-0010
- ADR-0011
supersedes: []
superseded_by: []
affected_repositories:
- egohygiene/mindgarden
affected_contracts: []
implementation_status: in_progress
evidence:
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/17
  description: Existing Quartz baseline and the bounded public v1 preview requirements.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/18
  description: The output contract precedes its portal-composition and deployment proofs.
exceptions: []
approval: null
---

# ADR-0013: Render reviewed v1 knowledge through the existing pinned Quartz adapter

## Context

Main contains reviewed v1 public discovery and a local registry. Quartz publishing
still reads v0 manifests. #17 explicitly selects the existing Quartz adapter as
the baseline. The maintainer authorized six bounded draft checkpoints, beginning
with a usable synthetic v1 preview, without ratifying proposed architecture.

## Decision

Propose a typed `x-site` adapter extension on the existing `projection/v1` record.
Reuse the public selection service, scope session, publication allowlists and
exact evidence already used by federation. Emit deterministic Markdown inputs,
typed selected-only links, logical citations and a useful empty selection.
Render reviewed content literally so source HTML and instructions stay inert.

Keep acquisition separate: source projection works offline; rendering consumes a
separately prepared exact Quartz commit and offline package cache. Build in an
owned temporary tree, using the pin's package lock and disabled install scripts.
The renderer is optional; Python/v0 and model-free CLI behavior remain available.

Use saved private plan digests and public immutable output manifests. Create or
verify outputs without replacing caller content. Represent only selected public
knowledge, canonical routes, renderer pin and artifact checksums. Private profile,
session, registry and physical-location digests never become public lineage.
Propose the minimal artifact contract before #18's full composition proof.

## Alternatives considered and rejected

A custom web framework would add a consequential choice beyond this checkpoint.
Exporting an internal index would expose control/denied metadata. Automatically
fetching the renderer in an offline session would merge acquisition with query
authority. Rendering arbitrary source HTML would grant executable behavior to
reviewed evidence. Replacing existing site folders would broaden destructive scope.

## Consequences and tradeoffs

Literal body rendering is intentionally limited; richer Markdown/assets need a
separate supported safety contract. Quartz's native navigation/search/graph remain
derived views, not canonical records. Native accessibility, mobile, large-corpus,
real consumer and runtime/network isolation evidence remain explicit follow-ups.

## Implementation and evidence links

The [six-checkpoint handoff](../garden-experience-milestone.md) records the draft,
targeted checks and remaining renderer/browser/consumer evidence.

## Replacement or exit strategy

Delete only separately owned generated state under a reviewed retention policy;
rebuild from canonical records. Replace Quartz through the adapter boundary while
preserving identifiers, citations and routes.

## Follow-up work

#18 owns portal integration; #38
owns stack-neutral design; #10 owns the conformance matrix; #42 owns human
disposition and broader application decisions. This ADR remains proposed/null
approval after implementation or merging.
