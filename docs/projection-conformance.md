# Projection conformance and synthetic reference envelope

The deterministic corpus recipe is committed under
[tests/fixtures/projection-corpus](../tests/fixtures/projection-corpus/recipe.json).
The generator creates synthetic reviewed notes, one claim, one typed relationship
and exact source evidence. It needs no archive, network, model or database.

The 32-note golden matrix covers index, graph, backlinks, outbound links, lexical
search, JSON context, Markdown context and `llms.txt`. JSON contracts validate the
projections and the embedded agent ledger. A fresh session reproduces exact bytes.
`outbound --artifact GARDEN/ID` uses existing graph authority; private/unavailable
endpoints never enter its map. Redaction qualifications retain only selected
source citations. Their presence does not weaken inherited sensitivity.

Context fitting uses a binary search over the reserved exclusion-ledger prefix.
The work-bound fixture proves logarithmic prefix serialization, then bounded
candidate selection with the same reasons and byte ceiling. No query result or
source body cache is introduced; live session/revocation/integrity checks remain.

## Measured envelope

```bash
python scripts/projection_benchmark.py --workspace /tmp/new-synthetic-corpus --records 1024
```

The script refuses a nonempty workspace and supports 2–4096 generated notes.
The **measured reference envelope is 1024**, with 1025 query candidates, 4 KB
context, at most 60 seconds per projection and 256 MiB peak process RSS. It fails
when the reference timing/memory ceiling is exceeded. Missing platform RSS support
is reported as `memory-unavailable`, not passing memory verification. The 4096
input bound is not a claim that its runtime/memory envelope has been verified.

Observed on Linux/Python 3.12.14 in this shared session:

| Projection | Seconds | Output bytes |
| --- | ---: | ---: |
| Index | 8.091 | 2323521 |
| Search | 13.294 | 2509 |
| Graph | 14.531 | 4017 |
| Backlinks | 16.568 | 2002 |
| JSON context | 16.573 | 3943 |
| Markdown context | 15.540 | 3840 |

Peak process RSS was 92,852,224 bytes (about 89 MiB), including corpus generation.
[The observed report](../tests/fixtures/projection-corpus/observed-linux-3.12.json)
records exact hashes; all six equal the pre-change run. Concurrent local checks
and host variation preclude treating these timings as a speedup guarantee or a
universal performance limit. Unit CI checks bytes, schemas, privacy and bounded
work; it does not impose a flaky wall-clock benchmark.

The private index exceeds the separate 2 MB federation-file limit. A public
federation export must use its own bounded reviewed selection. Larger reference
hardware/corpora, broader relationship matrices and consumer acceptance remain
parent scope. SQLite stays optional and is not made canonical by this checkpoint.
