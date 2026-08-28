# Extraction Record

Mindgarden's runnable v0 implementation graduated from
[`egohygiene/empathy`](https://github.com/egohygiene/empathy) at immutable
revision `f8313641fa05cb1d062057a426b094c0e3770522`.

The extracted source directory was `mindgarden/`; its Git tree at that revision
is `59edf41e612aacf8c4be5aa8d923392796e92d1e`.

## Method

The nine Empathy commits that changed `mindgarden/` were replayed as a
root-level history. Each extracted commit preserves the original subtree tree
evolution and message and adds an `Empathy-Source-Commit` trailer.
[`PROVENANCE.md`](PROVENANCE.md) records the complete immutable mapping.

This provides reviewable source history rather than a latest-tree copy while
allowing the pre-existing standalone architecture history to remain intact.

## Included inventory

- seven v0 JSON Schema contracts;
- dependency-free validation, ingestion, indexing, search, context-pack, and
  `llms.txt` commands;
- reviewed-public projection and pinned Quartz rendering adapters;
- Obsidian, agent, and Quartz profiles;
- unit tests, synthetic standalone fixtures, and standalone CI;
- MIT license and design provenance.

## Deliberately excluded

- Empathy's repository-owned `.garden/`, `.obsidian/`, and `llms.txt`;
- private overlays and generated `.cache/mindgarden/` state;
- Empathy task definitions, Pages composition, and integration tests that
  assert Empathy-specific content;
- any other Empathy source or repository history.

## Ongoing invariants

- This repository is the sole durable owner of reusable Mindgarden source.
- Mindgarden source does not import files from a consumer repository.
- Consumer knowledge stays in each consumer's `.garden/`, not in this source
  repository.
- Public interfaces are versioned contracts or documented commands.
- Tests and fixtures contain only synthetic, public-safe data.
- Consumers integrate through an immutable release, package, or commit.
- Third-party code and assets require recorded provenance and license review.

Empathy's consumer cutover is intentionally separate from the source
graduation. See [`docs/consumer-migration.md`](docs/consumer-migration.md).
