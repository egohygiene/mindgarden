# CozoDB optional projection evaluation — 2026-11-07

Proposed recommendation: **keep the removable experiment; defer adoption**.
The native adapter passes lexical, graph and provenance parity, but the measured
small corpus shows no query advantage over reference/SQLite and adds a native
binary/support boundary. No default dependency, canonical store, scope policy or
accepted ADR changes. The #33 evaluation is complete with this conservative defer outcome;
[the acceptance receipt](../overnight-sprint.md) records its criteria. Default
store adoption and ADR ratification remain separate human decisions.

## Exact software and portability

Evaluated [Cozo v0.7.6](https://github.com/cozodb/cozo/releases/tag/v0.7.6),
released 2023-12-11, commit `870f1e733f8e8aa2eb882c5653fc097981b95256`.
The actual pinned [LICENSE.txt](https://github.com/cozodb/cozo/blob/870f1e733f8e8aa2eb882c5653fc097981b95256/LICENSE.txt)
is **MPL-2.0**. No upstream source/assets are copied into the core. A future
redistribution/modification needs its own license/notice review. The repository
was unarchived, with its latest observed push dated 2024-12-04: this long release
and activity gap is a maintenance risk, not proof of abandonment or insecurity.

The installed package is **cozo-embedded 0.7.6**, CPython `cp37-abi3`,
`manylinux_2_17_x86_64.manylinux2014_x86_64`, SHA-256
`7571f6521041c13b7e9ca8ab8809cf9c8eaad929726ed6190ffc25a5a3ab57a7`.
The committed [artifact pin](../../experiments/cozo/requirements-linux-x86_64.txt)
is only for this tested Linux x86_64 wheel. PyPI lists Linux aarch64, macOS
x86_64/arm64 and Windows amd64 wheels; those OS/architectures were **not tested**.
Python 3.12.14 and 3.13.5 both passed the five native adapter cases using the
same abi3 artifact. Rust/C++ source builds, mobile, browser/WASM and alternate
engines are outside this checkpoint.

## Adapter and corpus

[The experiment](../../experiments/cozo/adapter.py) implements the existing
`QueryStore` methods over an already authorized v1 index. It stores records,
exact metadata, typed edges, backlinks and reference-token postings in the
native SQLite-backed Cozo engine. Parameterized Datalog selects lexical
candidates and graph adjacency; the existing reference ranker supplies unchanged
scores/reasons. It does **not** substitute native FTS ranking or vector similarity
for the public lexical contract. Native relation/checksum audits precede lookup;
backlink payloads must still equal the authorized view before emission.

[The shared synthetic corpus](../../experiments/corpus.py) has two public gardens,
reviewed knowledge/claims, exact source spans, cross-garden and local typed edges,
unreviewed canaries, and a separate personal garden/session overlay. The measured
public projection contains **262 records, two edges, 657,771 bytes**, with the
personal record excluded before indexing. Changing denied material leaves the
public view/results unchanged. Cross-session cache reuse and revoked sessions
fail before returning/opening cache content. Confidential/encrypted processing is
explicitly unavailable; this is not Realm #25/#60 runtime assurance.

The optional factory is exercised through the real application search service;
there is no installed `--cozo` flag. Core CLI restore currently compares the
SQLite backup envelope; the experiment restores by its own portable index
rebuild, not that SQLite-specific restore command. A generic installed selection,
restore dispatch and distribution contract would need a separate reviewed change.
Only the owned writer lock/quarantine helper is reused from the core SQLite
class; no Cozo code/dependency is imported by ordinary commands.

## Observed comparison and lifecycle

[Committed measurements](../../experiments/cozo/observed-baseline.json), Linux
x86_64/Python 3.12.14, one isolated process per adapter, 30 queries over six
literal/Unicode/adversarial terms:

| Adapter | Build ms | Query median / p95 ms | Peak process RSS KiB | Cache bytes |
| --- | ---: | ---: | ---: | ---: |
| In-memory reference | 0.000 | 0.361 / 0.563 | 36,732 | 0 |
| SQLite FTS5 | 108.472 | 55.238 / 62.051 | 36,732 | 1,892,807 |
| Cozo SQLite engine | 93.683 | 89.573 / 94.196 | 53,120 | 2,392,554 |

All result, score, reason and exact-source fingerprints agree. Both durable
adapters include full cache integrity audits per query; the reference already
holds its authorized index. RSS includes interpreter/modules/index initialization;
these are observations of this prototype, not general database rankings or
production sizing. Corpus creation/authorization is measured separately.
Portable backup observations are also in the report; native binaries and model
storage are not included in cache bytes.

Five explicit native cases prove rebuild/replay, parameter-safe lexical parity,
typed traversal/backlinks, private-overlay isolation and denied-content
noninterference, revocation before cache access, portable export/rebuild into a
fresh cache, actual native backup/restore, corruption refusal, incompatible
version refusal, retention of unknown files and staged-build failure cleanup.
Owned reset **quarantines** the cache for recovery rather than deleting originals.
An incompatible marker is rejected; an actual cross-release migration is not
claimed. The `python -S` exit probe rebuilds/searches through reference/SQLite
with Cozo unavailable and the experimental adapter never imported. Canonical
records remain outside the optional cache.

A separate [native probe](../../experiments/cozo/native_probe.py) tests actual
FTS matches and HNSW nearest-neighbor behavior on two-dimensional authored
vectors. [Its receipt](../../experiments/cozo/observed-native.json) claims neither
semantic quality nor ranking parity. The Garden adapter still declares vectors,
native FTS, encryption, incremental updates and multiple writers unsupported.
No model is called. Native execution succeeded in the default network-denied
sandbox. A syscall trace was attempted, but `strace` failed because ptrace is
denied; no syscall-level telemetry/egress assurance is claimed.

## Reproduce and decide

Install in a disposable environment, never the core runtime:

```sh
python3 -m venv --without-pip .cache/evaluations/cozo-python
python3 -m pip --python .cache/evaluations/cozo-python/bin/python install \
  --only-binary=:all: --require-hashes \
  --requirement experiments/cozo/requirements-linux-x86_64.txt
.cache/evaluations/cozo-python/bin/python -m unittest experiments.cozo.test_adapter -q
.cache/evaluations/cozo-python/bin/python -m experiments.cozo.benchmark \
  --records-per-garden 128 --report /tmp/cozo-observed.json
.cache/evaluations/cozo-python/bin/python -m experiments.cozo.native_probe \
  --report /tmp/cozo-native.json
python3 -S -m experiments.cozo.exit_probe
```

The test corpus/temp caches are owned and cleaned by the experiment. To leave,
retain canonical Garden/vault data, remove only the disposable environment/cache
and experimental consumer wiring, and rebuild the reference/SQLite projection.
No absolute machine locations, credentials or native identifiers enter portable
records. Production data must not enter this lab.

Revisit when native graph query/incremental workloads show a measured benefit,
the support/upgrade and install/restore contracts are supplied, or an owner
accepts a maintained pinned binary. A future vector trial needs its own model,
quality, policy and cost evidence. Review again by 2027-01-01. Until then, the
portable file engine and optional SQLite remain the supported baseline.
