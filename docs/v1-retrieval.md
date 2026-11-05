# Reviewed v1 retrieval and bounded context

This is the first practical local usability checkpoint under #12. The shared
services in `mindgarden.application.retrieval` index knowledge and claims,
construct typed graphs/backlinks, explain lexical ranking and render bounded
context. The CLI invokes those services. V0 commands and library calls retain
their existing behavior; v1 requires explicit authorized inputs.

## Explicit inputs

Supply `--local-config` with external bindings and `--scope` with a
`mindgarden.session/v1` JSON file. Readable entries pin garden fingerprints;
`garden_fingerprint` in the application bindings module computes them without
host paths or generated caches. Session policy matches `POLICY_REFERENCE` in the
domain scope module. Session IDs, scopes, projections, review states, budgets,
expiration and a nullable writable target are explicit. Never copy a real local
binding file into the public repository.

The session can optionally classify request/query data with `request_scope`.
Omission defaults to personal: public sources do not automatically make a private
query or its metadata public. Publication authority remains independent of review.
Public generated output requires publishable authority and only eligible reviewed
knowledge; ordinary local context is private and has no publication authority.

## Commands

All v1 commands use the same `--repository-root`, `--local-config` and `--scope`
arguments. Search uses `--query` and `--limit`; `--include-unreviewed` cannot
exceed the supplied session's allowed review states. Reviewed active knowledge
is the default, and raw sources never become ordinary knowledge search results.

- `mindgarden index` previews JSON; `--write` and `--check` manage the owned index.
- `mindgarden search --query "prompt"` returns exact evidence and score reasons.
- `mindgarden graph --start "garden-id/artifact-id" --max-depth 2` traverses typed links.
- `mindgarden backlinks --artifact "garden-id/artifact-id"` returns authorized incoming links.
- `mindgarden context --pack "default" --format "json"` renders bounded context.
- `mindgarden llms` renders an authorized local entrypoint.
- `mindgarden verify` independently rebuilds and compares authorized indexes.

New gardens include a reviewed `default` context profile. Existing gardens can
add a conforming `mindgarden.context-profile/v1` record through reviewed authoring;
there is no silent in-place template upgrade. `build_index(root,
query_context=context)` and `search_payload(..., query_context=context)` extend
the existing library functions. Shared v1 services are also directly importable.

## Evidence and deterministic output

Indexes carry knowledge/claim identities, represented content revisions, source
selectors, review and sensitivity. Edges retain their types and review boundaries.
Ranking has fixed body/title/heading/tag weights plus explicit domain/topic
contributions, with stable identity tie-breaking. Search snippets contain only
selected authorized records; physical vault paths are never output.

Context profiles bound item count, candidate count and serialized UTF-8 bytes.
JSON and Markdown retain a selection ledger, source hashes, review, scope and
score contributions. The builder reserves exclusion metadata, considers a
bounded candidate window and includes whole items only. Too-small mandatory
metadata budgets fail explicitly. Markdown fences cannot be closed by embedded
source backticks. Enclosed text is structurally untrusted evidence.

Projection writes require the explicit writable target and a compatible output
scope. They remain under the garden's first declared generated root and refuse
unowned nonempty directories. V1 `context --output` is a relative filename under
that owned root; v0 retains its existing output argument semantics. Indexes and
entrypoints are rebuilt, not promoted into canonical knowledge.

## Checkpoint verification and remaining boundary

```bash
.venv/bin/python -m unittest tests.test_v1_retrieval --verbose
```

The synthetic test initializes a private v1 garden, imports text into a separate
vault, authors reviewed knowledge/claims/relationships, searches exact evidence,
renders bounded context and rebuilds through both CLI and library services.
Moving the garden root without changing records produces identical projections.
Networking and model services are unnecessary.

The full adversarial per-record, generated-metadata and cache isolation audit is
the later #31 checkpoint. This bounded #12 result does not claim federation,
consumer publication, broad scale acceptance or runtime isolation assurance.
