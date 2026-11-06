---
schema: egohygiene.architecture-decision/v1
id: ADR-0012
title: Manage local registrations without changing canonical gardens
status: proposed
date: "2026-11-05"
decision_scope: repository
visibility: public
owners:
- egohygiene/mindgarden
issue: https://github.com/egohygiene/mindgarden/issues/30
pull_request: https://github.com/egohygiene/mindgarden/pull/67
related:
- ADR-0008
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
  url: https://github.com/egohygiene/mindgarden/issues/30
  description: Owning local registry and private-overlay requirements.
- type: issue
  url: https://github.com/egohygiene/mindgarden/issues/31
  description: View selection never expands session authority or weakens output sensitivity.
exceptions: []
approval: null
---

# ADR-0012: Manage local registrations without changing canonical gardens

## Context

Main now contains the authorized private workflow and public projection checkpoints
through #66. Explicit `local-bindings/v1`, scope and session contracts already
exist. #30 needs a usable registration lifecycle rather than another garden model.
The user authorized implementation of this bounded tool capability with synthetic
gardens; real consumer setup remains a separate explicit operation.

## Decision

Propose optional `registry` management metadata inside the existing machine-local
binding document. Preserve its garden/vault bindings and revocation authority.
Canonical IDs, owners and scope come from the existing v1 manifest; registration
asserts them rather than editing sources. Registration reads only the explicit
manifest, not notes, transcripts, attachments or arbitrarily discovered folders.

Use separate saved preview and digest-bound apply operations. Bind the control
location, previous/desired registry hashes, exact manifest bytes and root identity.
Apply atomically replaces only the private registry, under a POSIX kernel writer
lease, and preserves checksum-bound private configuration snapshots. Re-applying
an identical accepted plan verifies the desired state. Unregister removes the
binding/labels and prunes named selections, preserving all canonical files and
vaults. Query-cache cleanup and destructive retention remain separate.

Named views select registered IDs; they never grant visibility, network, write,
publication or review authority. Sessions still require the existing explicit
grants. Per-view monotonic generations invalidate sessions after membership/removal
changes. Restore preserves explicit revocations and advances view generations so
old named grants cannot silently revive. Runtime readers ignore unrelated private
management labels; named sessions validate their selected view before root probes.

Store control state in platform user configuration, or an explicitly supplied
dedicated private directory disjoint from garden/vault ownership and actual Git
workspaces. The boundary covers leases, staging, history and recognized
unregistered garden roots as well as the registry file. Local plans,
snapshots, labels, paths and registry identities are never public projection
lineage. Preserve the existing additive v0/v1 APIs and dependency-free Python
engine. Ordinary Linux filesystem operations are the bounded baseline.

## Alternatives considered and rejected

A new canonical garden database would duplicate ownership. Crawling home/cloud
folders would expand data access. Editing repository configuration would publish
machine state. Rewriting canonical identity/scope during registration would mix
setup with consequential content changes. Blind unregister deletion would risk
originals. Restoring revocation state backwards or reusing view generations could
revive old sessions. A default public fallback would weaken scope.

## Consequences and tradeoffs

Private metadata history is retained until a separately reviewed policy authorizes
cleanup. Doctor verifies registration/manifest health, not every source hash or
runtime assurance control. Platform location resolution has synthetic Linux,
macOS and Windows fixtures. Linux was the initial mutation baseline; draft #93
adds bounded native macOS evidence, while Windows remains unsupported.
Restricted/encrypted registration fails before root probes
because compatible Hygiene/Realm assurance evidence remains unavailable. This does
not implement encryption, sync, acquisition, hosting or a confidential runtime.

The local reference implementation is explicitly authorized; this ADR remains
proposed with null approval. Code review and merging do not ratify it.

## Implementation and evidence links

See [the registry checkpoint](../local-registry.md), [coverage ledger](../open-issue-coverage.md)
and CONTINUITY.md for the draft, functional commits, commands and exact next action.
Fixtures use synthetic roots and private temporary configuration only.

The [native macOS follow-up](../registry-native-platforms.md) adds an ordinary
adapter with native extended-ACL and physical-path checks. Its successful native
CI evidence is separate from Linux fixtures and from restricted/host assurance.
This extension does not change the proposed status or null approval of this ADR.

## Replacement or exit strategy

Canonical gardens remain independently readable. Existing explicit bindings work
without registry metadata. Export or restore owned private configuration through
reviewed plans; a new implementation can consume the same versioned bindings and
view selection contracts. Incompatible format or authority changes require
separate decisions and migration proof.

## Follow-up work

Human disposition; #30 native platforms/restricted/runtime and owned-cache cleanup;
#29/#31 normative policy integration; Realm #25/#60 host assurance; Hygiene #39/#40;
#14 relocation/transfer integration; #46 control-history retention; broader #42/#47
product decisions. No parent issue is completed by this bounded checkpoint.
