# Mindgarden Architecture

## Architectural intent

Mindgarden is a local-first knowledge substrate. A repository's `.garden/`
directory is canonical; every user interface, search index, agent integration,
and published site is an adapter or derived projection.

## Layers

1. **Knowledge contract** — versioned manifests, Markdown notes, YAML
   frontmatter, stable identifiers, provenance, confidence, and lifecycle.
2. **Garden engine** — initialization, validation, migration, indexing, and
   deterministic transformations.
3. **Adapters** — Obsidian configuration, agent CLI/MCP access, search, and
   GitHub Pages publishing.
4. **Consumer gardens** — repository-owned `.garden/` instances such as
   Empathy's initial garden.

Dependencies flow downward from consumer adapters toward the knowledge
contract. The knowledge contract cannot depend on Obsidian, a particular LLM,
an embedding provider, or a site generator.

## Source and projection boundary

- Markdown and YAML committed under `.garden/` are durable source.
- Generated indexes, embeddings, caches, and rendered sites are disposable.
- Deterministic ingestion records the supplied artifact, declared origin,
  transformations, and hashes without fetching or interpreting the source.
- Agent search and context packs are bounded projections with explainable
  lexical ranking; reviewed knowledge is the default trust boundary.
- Agent-authored knowledge enters as `draft` or `proposed` and remains visibly
  unreviewed until a human promotes it.
- A public repository may commit only public garden material.
- Private or internal material belongs in an ignored external overlay such as
  `.garden.local/`, not in a build-exclusion convention.

## Incubation boundary

During incubation, `mindgarden/` owns reusable capability source while the
repository-root `.garden/` is Empathy's consumer instance. Code inside this
directory must not import Empathy internals. Empathy may invoke Mindgarden only
through documented commands and versioned contracts.

This direction preserves the option to extract `mindgarden/` into its own
repository without rewriting its implementation.
