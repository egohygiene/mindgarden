# Consumer migration

This guide separates Mindgarden source ownership from a consumer repository's
knowledge ownership. Empathy is the first golden consumer, but the sequence
applies to any repository moving from an embedded copy.

## Ownership after graduation

- Mindgarden owns reusable schemas, commands, profiles, tests, and releases.
- The consumer owns `.garden/`, `.obsidian/`, `llms.txt`, publication identity,
  workflow composition, and any private `.garden.local/` overlay.
- Generated indexes, projected Markdown, Quartz checkouts, and rendered sites
  remain disposable consumer cache state.

## Cutover sequence

1. Pin an immutable Mindgarden release, package, or full commit SHA in the
   consumer's build interface.
2. Materialize that tool outside the canonical `.garden/`, such as beneath an
   ignored tool cache.
3. Move the consumer's Quartz profile and configuration to
   `.garden/publishing/quartz.yaml` and
   `.garden/publishing/quartz.config.yaml`.
4. Replace invocations of the embedded `mindgarden/scripts/` copy with the
   pinned tool path while preserving `--repository-root` as the consumer root.
5. Run validation, agent verification, and public-projection verification
   against the unchanged consumer garden.
6. Remove the embedded implementation only after the pinned interface passes
   the consumer's integration and Pages workflows.

Example verification through an installed, pinned Mindgarden package:

```bash
mindgarden validate --repository-root "/path/to/consumer"
mindgarden verify --repository-root "/path/to/consumer"
mindgarden publish verify --repository-root "/path/to/consumer"
```

## Compatibility and recovery

The first cutover should preserve the v0 schemas and command behavior exactly;
v1 migrations belong in a later reviewed change. A rollback changes only the
pinned tool revision. It must not rewrite, delete, or restore consumer knowledge
from generated projections.

The source extraction does not itself switch Empathy. That independent change
must cite its exact Mindgarden revision and retain consumer-owned integration
tests for `.garden/`, Obsidian, agent context, and Pages composition.
