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

Example verification from a Mindgarden checkout:

```bash
python3 scripts/validate_garden.py --repository-root "/path/to/consumer"
python3 scripts/garden_agent.py --repository-root "/path/to/consumer" verify
python3 scripts/publish_garden.py --repository-root "/path/to/consumer" verify
```

## Compatibility and recovery

The first cutover should preserve the v0 schemas and command behavior exactly;
v1 migrations belong in a later reviewed change. A rollback changes only the
pinned tool revision. It must not rewrite, delete, or restore consumer knowledge
from generated projections.

The source extraction does not itself switch Empathy. That independent change
must cite its exact Mindgarden revision and retain consumer-owned integration
tests for `.garden/`, Obsidian, agent context, and Pages composition.
