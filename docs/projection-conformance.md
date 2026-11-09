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
The initial **measured reference envelope was 1024**, with 1025 query candidates, 4 KB
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
federation export must use its own bounded reviewed selection. Wider hardware and larger corpora are future qualification opportunities;
the relation matrix is extended below. These do not add unstated #12 gates. SQLite stays optional and is not made canonical by this checkpoint.

## Extended relation/selection and 2048-note checkpoint

The new matrix exercises all eight existing synapse types, directed/undirected
backlinks, exact claim citations and cross-garden references. Unavailable and
denied targets do not change index, search, graph, backlink, outbound or either
context format. A selected context retains the original live session and uses a
distinct cache identity; unselected bodies and unavailable unselected roots are
not opened. Omitted cross-garden dependencies fail closed on revision mismatch.

The same benchmark ran with `--records 2048`: 2049 candidates, one claim, one typed
edge and 4 KB context. Linux/Python 3.12.14 observations:

| Projection | Seconds | Output bytes |
| --- | ---: | ---: |
| Index | 15.282 | 4641857 |
| Search | 27.170 | 2509 |
| Graph | 28.195 | 4017 |
| Backlinks | 28.402 | 2002 |
| JSON context | 26.709 | 3943 |
| Markdown context | 26.847 | 3840 |

Peak process RSS was 166,473,728 bytes (about 159 MiB). All six operations pass the
same 60-second/256-MiB synthetic reference bounds, with networking blocked. This
extends the observed envelope rather than guaranteeing interactive latency or
arbitrary hardware/corpora. Full live authorization/integrity checks remain; no
cache becomes authority and no database is required. The 4096 generator cap remains
unqualified. The expanded relation matrix uses a small corpus; the 2048 benchmark
uses the simpler recorded recipe, not every relationship at scale.

The committed larger report and fresh-context repeat receipt record exact hashes.
The fresh context reproduces the index and JSON context bytes. Existing 32-note
full projection goldens remain unchanged. Rendered whole-site performance and
wider real consumer acceptance are separate work. These timings justify future
profiling for interactive use; this checkpoint makes no unsupported speedup claim.
