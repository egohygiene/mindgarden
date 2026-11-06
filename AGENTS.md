# Repository release work

Before changing release behavior, read [the release guidance](docs/releases.md),
[the declaration](.egohygiene/release.json), the changelog and pinned owner inputs.
`pyproject.toml` owns the Python package version; runtime versions are derived.

Use the plan, prepare and verify Taskfile handoffs to produce a reviewable
candidate. `release:publish` only hands an already reviewed default-branch
candidate to the manual workflow. Ordinary PRs never publish. Preserve immutable
tags/assets and record unavailable external evidence honestly.

Keep the Python engine, v0 compatibility and source/projection boundaries. Use
synthetic fixtures here; real archives, credentials, consumer paths and private
data remain outside this public repository. Update CONTINUITY.md and the coverage
ledger after each bounded checkpoint. Proposed ADRs retain their current status.
