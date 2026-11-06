# Native registry platform checkpoint (#30)

This follow-up extends the merged [registry/cache checkpoint](local-registry.md)
on `feature/30-macos-registry-conformance`, based on main
`d5edb13de1b65871ec85e7a25af035228a1d756d` (merged #92). It implements a bounded
ordinary single-user macOS adapter and native conformance job. The initial local
checks run on Linux; native support remains a candidate until the macOS jobs
actually pass. The draft PR and final verification are recorded below and in
CONTINUITY.md. Refs #30; this does not complete its parent acceptance criteria.

## Dependency and ownership reconciliation

The requested #29 → #31 → #30 → #35 → #45 checkpoints are already merged in
#80–#84. See [the merge receipts](merged-pipeline-storage-checkpoints.md).
They should not be rebuilt or closed as complete. #92 adds the deferred
#86–#91 roadmap without scheduling its features.

Native ordinary registry controls can be proved independently of a confidential
runtime. #29/#31 still own scope/policy authority; registry view selection never
expands it. Hygiene #39/#40 and Realm #60 remain open owner-contract/assurance
gates. Nothing in an ordinary macOS test supplies an organization policy,
encrypted storage, remote provider or confidential host guarantee. Windows
mutation remains explicitly unsupported. This is a bounded dependency correction,
not a bypass of those gates or a new garden model.

The existing proposed [ADR-0012](decisions/ADR-0012-machine-local-registry.md)
retains null approval. Its local filesystem adapter boundary owns the extension;
the application services, canonical garden records and portable contracts remain
unchanged. No source acquisition, model integration or new runtime dependency is
introduced.

## Filesystem contract

Linux retains the existing single-user POSIX baseline. macOS additionally queries
the native extended ACL on each opened private control file/directory, including
plans, writer leases, staging and history. Modes 0600/0700 alone do not establish
the macOS boundary. Any extended entry, including a restrictive entry, is rejected
without editing permissions. An absent or validated empty ACL is allowed;
unavailable interfaces, unknown results and failed verification are denied before
reading private control bytes or writing their content. Only API bindings are
cached, never ACL decisions.

Native macOS paths must use the exact physical on-disk spelling. `F_GETPATH`
checks the opened control path and explicitly selected existing ownership roots.
An alias that differs in case is refused instead of silently creating a second
logical root over the same files. Existing symlink/traversal and ownership-overlap
checks still apply. Synthetic temporary fixtures resolve their own system temp
alias; the runtime does not silently rewrite user bindings. Old noncanonical
bindings require explicit correction. Unselected roots are not probed to perform
this check, and unsupported scope is still denied before a root probe.

Runtime checks call native APIs through Python's standard library; they do not
shell out. Native fixture setup alone invokes `/bin/chmod` to add an actual ACL.
Controls stay outside Git workspaces and garden/vault roots. No canonical content
is moved, migrated, deleted or reclassified by registration or these checks.

## Native interface evidence

Only public interfaces/constants are used; no Apple implementation was copied.

- Apple Libc [`sys/acl.h`](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/include/sys/acl.h),
  [`acl_get_entry(3)`](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/posix1e/acl_get_entry.3)
  and [`acl_get_fd(3)`](https://github.com/apple-oss-distributions/Libc/blob/71bbe350ab79eef58113991d817ccc6165061a64/posix1e/acl_get_fd.3),
  pinned at `71bbe350ab79eef58113991d817ccc6165061a64`, establish
  `ACL_TYPE_EXTENDED`, `ACL_FIRST_ENTRY`, `acl_get_fd_np`, `acl_valid`,
  `acl_get_entry` and `acl_free`. The empty-entry and absent-property results
  were checked against that revision's `acl_entry.c`, `acl_file.c` and
  `gen/filesec.c`: a validated empty ACL has no first entry (`-1`, `EINVAL`);
  an absent ACL property returns `ENOENT` on an already-open descriptor.
- Apple XNU [`fcntl.h`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/sys/fcntl.h)
  and [`syslimits.h`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/sys/syslimits.h),
  pinned at `f6217f891ac0bb64f3d375211650a4c1ff8ca1ea`, establish
  `F_GETPATH = 50` and `PATH_MAX = 1024`.

These source references explain the bridge; actual native execution, not source
inspection or mocked platform names, is the compatibility proof.

## Verification and recovery

[The automatic workflow](../.github/workflows/test.yml) adds standard `macos-15`
jobs on Python 3.12 and 3.13. They record the host, run native ACL/path tests plus
the existing registry lifecycle, views and reversible cache cases, then build
and install the wheel into a clean environment. The installed ordinary CLI demo
must reproduce the unchanged registry golden with networking, external processes,
Google and model calls blocked or unused. No workflow is manually dispatched.

The native tests include real ACL grants on otherwise-private files, directories
and writer leases. A case alias must be denied on a case-insensitive volume; on
a case-sensitive volume it must remain a distinct missing file/directory. Portable
adversarial ACL doubles verify denial before any private byte read, interface
unavailability and cleanup. Doubles do not count as native platform evidence.

| Command/check | Observed result |
| --- | --- |
| `.venv/bin/python -m unittest tests.test_registry_acl tests.test_registry tests.test_registry_views tests.test_registry_cache -q` | 39 passed on Linux/Python 3.12.14; 35.692 s |
| `.cache/python313/bin/python -m unittest tests.test_registry_acl tests.test_registry tests.test_registry_views tests.test_registry_cache -q` | 39 passed on Linux/Python 3.13.5; 35.230 s |
| `python3 .cache/context_phase_owner_checks.py` | Pinned owner validators pass; proposed/null-approval ADRs, continuity and all 44 coverage rows retained |
| `git diff --check`; compile sources | Pass |
| `.venv/bin/python -m build --sdist --wheel --outdir .cache/dist`; `.venv/bin/python -m unittest tests.test_distribution -q` | Fresh source/wheel built; 2 packaging tests passed, including both new adapters |
| Native macOS and full compatibility suite | Pending; do not claim verified support until recorded |

Full #30 remains open for unsupported platforms, restricted/encrypted coexistence,
organization/runtime assurance and real private consumer acceptance. Broader
#29/#31 policy integration, #35 confidential/OCR/office ingestion, and #45
provider/power-loss/approved-copy/destructive-retention proofs remain separate.

The exact next action is to publish the coherent draft, inspect the automatic
native jobs, correct observed failures, and record their actual result alongside
the complete Linux compatibility and installed-wheel checks. Leave the new PR
for maintainer review; do not self-ratify the proposed ADR or start #86–#91.
