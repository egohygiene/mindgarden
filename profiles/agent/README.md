# Agent Profile

The agent profile exposes a dependency-free CLI over the same committed
Mindgarden Markdown used by humans. It is the portable baseline for Codex,
Claude Code, Copilot, local scripts, and future MCP adapters.

The core performs no model calls, remote fetching, embedding, or background
writes. Agents may acquire and interpret material outside Mindgarden, but every
durable operation crossing into the garden is explicit, validated, and
reproducible.

## Verify

Run the complete agent projection contract:

```bash
python3 scripts/garden_agent.py \
  --repository-root "/path/to/consumer" \
  verify
```

Verification rebuilds the catalog and context packs twice, compares their bytes,
checks context budgets, validates provenance hashes, and confirms that the
committed `llms.txt` matches canonical knowledge.

## Search

Search uses a fixed lexical score over titles, tags, headings, and body term
frequencies. Results include the contribution of each matched term, so agents do
not receive an opaque relevance score.

```bash
python3 scripts/garden_agent.py \
  --repository-root "/path/to/consumer" \
  search \
  --query "architecture decisions" \
  --limit 5
```

Only human-reviewed knowledge is returned by default. An explicit
`--include-unreviewed` flag is required to search drafts and proposals.

## Context packs

Context-pack profiles are canonical YAML under `.garden/context-packs/`. They
declare stable inclusions, exclusions, lifecycle filters, and character and note
budgets.

```bash
python3 scripts/garden_agent.py \
  --repository-root "/path/to/consumer" \
  context \
  --pack "example-agent-default" \
  --format "markdown"
```

Markdown packs label every note with its path, SHA-256 digest, review status,
confidence, and declared sources. Note bodies are structurally delimited and
accompanied by an instruction boundary. JSON output is also available for
runtime adapters.

## Indexes

The deterministic catalog contains stable metadata, hashes, headings, word
counts, and lexical term frequencies. It contains no wall-clock generation
timestamp, embeddings, absolute host paths, or hidden database state.

```bash
python3 scripts/garden_agent.py \
  --repository-root "/path/to/consumer" \
  index \
  --write
```

Materialized indexes live under the ignored `.garden/.index/` generated root.
A clean clone does not need a prebuilt index: search and context commands rebuild
the current catalog in memory.

## Ingestion and provenance

Ingestion accepts only a supplied regular UTF-8 text file. It never follows a
URL, invokes a model, guesses a capture date, or overwrites an existing artifact.
The default is a read-only plan:

```bash
python3 scripts/garden_agent.py \
  --repository-root "/path/to/consumer" \
  ingest \
  --input "/path/to/source.md" \
  --source-id "source-example" \
  --title "Example source" \
  --origin "https://example.com/source" \
  --captured "2026-08-14" \
  --owner "egohygiene" \
  --rights "Reference-only; verify upstream terms"
```

After reviewing the paths and hashes, repeat the command with `--write`. A
public garden additionally requires `--confirm-public` so a fetched private
artifact is not committed through an implicit visibility assumption.
Mindgarden creates:

- a proposed, unreviewed source note under `.garden/sources/`;
- a canonical JSON provenance record under `.garden/provenance/`.

The provenance record binds the origin, normalized-content hash, generated note
hash, media type, capture date, rights statement, and exact deterministic
transformations. Validation fails if the artifact changes without a matching
provenance update.

## Safety boundary

- Generated indexes and context output are disposable.
- Imported sources remain proposed and unreviewed.
- Default search and context profiles exclude unreviewed material.
- Context packs label content as evidence rather than executable instruction.
- Paths supplied for generated context output cannot escape the generated root.
- Ingestion rejects symlinks, non-UTF-8 content, oversized inputs, traversal by
  stable identifiers, and replacement of existing notes.
- Writes into a public garden require an explicit `--confirm-public` gate.
- MCP, semantic indexes, and model-assisted synthesis may wrap this CLI later;
  they must not become a second source of truth.
