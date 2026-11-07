# OpenViking optional context/memory evaluation — 2026-11-07

Proposed recommendation: **adapt the tiered-context idea; defer runtime adoption**.
A removable producer preserves selected Garden evidence, but no useful native
no-model service was established. This is a documented blocked experiment,
not a supported agent integration, accepted ADR or replacement canonical store.
#34 remains open for maintainer disposition and missing runtime evidence.

## Exact inputs and official evidence

Evaluated [OpenViking v0.5.3](https://github.com/volcengine/OpenViking/releases/tag/v0.5.3),
released 2026-11-02, commit `178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8`.
The repository was unarchived and active on 2026-11-07; recent activity does not
establish long-term support. The actual pinned
[LICENSE](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/LICENSE)
is **AGPL-3.0**. A modified/networked deployment or redistributed integration
requires an owner-reviewed license/notice/source-offer disposition; no upstream
code/assets are copied into Mindgarden and no such deployment is authorized here.
This is not a full transitive dependency/model license audit.

Pinned source references:

- [pyproject](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/pyproject.toml): Python >=3.10;
  provider, parsing, vector/native-storage, HTTP/server and telemetry dependencies.
- [L0/L1/L2](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/docs/en/concepts/03-context-layers.md):
  abstract/overview are directory-level semantic sidecars. Ordinary files do not
  necessarily have both; accessor/search views hide metadata. Unknown sidecar
  fields are dropped. Generated-body budgets are not hard stored-byte ceilings.
- [Storage](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/docs/en/concepts/05-storage.md):
  AGFS/RAGFS content and vector stores are separate; indexed abstracts/memory
  can contain readable text. The documented new local record format is readable
  by new versions, but older executables cannot read it; downgrade needs a
  pre-upgrade backup. Filesystem operations may have partial/asynchronous effects.
- [Session memory](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/docs/en/concepts/08-session.md):
  commit archives messages then schedules summary/extraction; task acceptance
  is not completion. Extraction may add, edit, merge or delete memories.
- [Resource ingestion](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/docs/en/api/02-resources.md)
  and [configuration](https://github.com/volcengine/OpenViking/blob/178a8cdfb41b51e7d24c4bf79a13cc54981e0ee8/docs/en/configuration/01-server.md):
  local files, URLs/crawlers and optional external parsers/providers are distinct
  trust boundaries. Unknown configuration fields can be ignored with warnings;
  Garden policy cannot be enforced merely by adding custom keys to `ov.conf`.

The actual installed wheel is **openviking 0.5.3**, Linux x86_64
`cp310-abi3-manylinux_2_31`, SHA-256
`e3b3d72a4d40c1d246d0547d74505ac677f924463205c85115601bd16e2002ae`;
its installed **openviking-sdk is 0.1.18**. The isolated pip install resolved
**320 distributions**, about **1.3 GiB** for the environment, including LiteLLM,
provider SDKs, HTTP/server/parsing/tokenizer and OpenTelemetry components.
The [observed wheel lock](../../experiments/openviking/requirements-linux-x86_64-python312.txt)
records all exact installed versions/hashes for this Linux/Python 3.12 trial.
It is not a cross-platform lock, security audit or core dependency declaration.
`pip check` reports no broken requirements. Python 3.13/other platforms were
not used for the native service; only the dependency-free producer was tested
on both Python versions.

## What actually ran

[The native probe](../../experiments/openviking/native_probe.py) supplies its own
synthetic config, data/model/cache/log locations, missing local GGUF path,
loopback-only placeholder VLM URL, disabled tracer and recorder. It never reads a
real archive or starts the HTTP server. Inherited proxy/CA configuration remains
intact. Python HTTP calls are denied and the process runs in the default
network-denied sandbox; no remote or local model is supplied/downloaded.

[The committed observation](../../experiments/openviking/observed-native.json)
records the distinction between installed, constructed, blocked and unverified:

| Surface | Actual observation | Limit |
| --- | --- | --- |
| Python API | `SyncHTTPClient` exists; old `OpenViking()` embedded facade does not | Do not implement against an older guessed API |
| Native config | Explicit workspace resolves inside the owned directory; tracer disabled; default server is `127.0.0.1:1933` | No HTTP server was launched; no proof about every native bind/telemetry path |
| Unknown policy | An unknown required-scope field was accepted/dropped | The producer rejects unsupported scope; upstream config is not policy authority |
| Network | One Python HTTP attempt during LiteLLM import was blocked; warning identifies remote model-cost metadata | Local/no-model intent alone is insufficient to claim no network behavior; syscall tracing is unavailable because ptrace is denied |
| Model | Explicit missing local file raises `EmbeddingConfigurationError` | No semantic retrieval/summary or model quality result |
| Service/storage | Constructor passed and wrote owned runtime state; initialization timed out; supervised attempt ended after about 25 seconds during partial close | A constructible object is not a usable service or successful graceful recovery |
| Resource observation | About 433,800 KiB peak child RSS; 108,215 bytes of owned lab state; environment footprint measured separately | Blocked startup cost only, not steady-state or useful-query benchmark |
| Cleanup | Supervisor removes the entire owned temporary lab after stopping the child | Not production secure erasure or native backup/restore evidence |

A first unsupervised 45-second attempt also timed out; its known synthetic
workspace was verified and removed. The supervised probe preserves partial
progress, records timeouts and removes only its own root. No missing runtime
step is converted into a passing comparison.

## Removable producer and provenance boundary

[The adapter](../../experiments/openviking/adapter.py) accepts only explicit
reviewed public references through the existing authorized services. It generates
exact Markdown evidence leaves plus a separate Garden provenance map, checks byte
budgets and retains logical IDs, represented revisions, source spans/hashes,
review, scope, attribution and uncertainty. It neither imports the SDK nor
uploads raw source vaults. Proposed `viking://resources/mindgarden/...` locations
are **unverified destinations**, not claimed native ingestion results.

The verified-leaf resolver rechecks current authority and canonical selections,
then requires the exact mapped URI and bytes before returning current Garden
evidence. Tampered maps/content, unmapped summaries, denied inputs, expired or
revoked authority fail. L0/L1 summaries and search snippets cannot inherit human
review or exact citations merely because they mention a Garden ID. An actual
native upload/segmentation/returned-URI binding still needs a live contract test.

Four dependency-free producer cases prove deterministic selected output,
qualifications and exact citations, no-model operation, tampered/unmapped-leaf
refusal, public/private scope separation, unsupported memory/budget refusal,
portable bundle copy/restore, canonical-location relocation/rebuild, unchanged
originals and removal. [The golden](../../experiments/openviking/expected-producer.json)
is a **producer** proof, not a mocked successful OpenViking backend.

Session memory is deliberately **disabled and unavailable** in the adapter.
Enabling it fails explicitly. Native scoped session creation, inspect/delete,
archive/summary/embedding retention and #46 cleanup remain unverified. Never
let a model's memory edits/deletions overwrite reviewed canonical knowledge.

## Acceptance gaps and comparison

The #32 reference/SQLite and #33 Cozo measurements provide a common baseline.
OpenViking quality, useful-query latency, steady-state memory/disk, ingestion,
context tiers, rebuild throughput and session benefits are **blocked**, so there
is no meaningful native ranking/performance comparison. A 25-second timeout and
import footprint cannot substitute for such evidence.

Producer backup/restore/rebuild/removal is tested. **Native** AGFS + vector
backup/restore, real cross-version upgrade/downgrade, partial initialization
recovery, reset, session deletion, encrypted-volume containment and complete
state inventory remain blocked. The documented one-way storage format means
upgrades require actual backup/downgrade trials, not a version-marker edit.
Personal/restricted data are refused by this lab, not declared protected inside
OpenViking. Swap, subprocesses, logs, caches, vectors, prompts, model downloads,
telemetry, keys and all state need a verified runtime boundary before private use.

Live [Realm #25](https://github.com/egohygiene/realm/issues/25) routes continuing
runtime acceptance to [#60](https://github.com/egohygiene/realm/issues/60); host,
released-producer and confidential proof remain open. Live
[Aether #64](https://github.com/egohygiene/aether/issues/64) still requires an
evidence-backed capability manifest and real integration pilot. No compatible
accepted runtime/agent promise is inferred from package installation or closed
foundation issues. These owner gates do not block the independent public
producer/evaluation checkpoint.

## Reproduce, exit and revisit

```sh
python3 -m venv --without-pip .cache/evaluations/openviking-python
python3 -m pip --python .cache/evaluations/openviking-python/bin/python install \
  --only-binary=:all: --require-hashes \
  --requirement experiments/openviking/requirements-linux-x86_64-python312.txt
python3 -m pip --python .cache/evaluations/openviking-python/bin/python check
.cache/evaluations/openviking-python/bin/python -m experiments.openviking.native_probe \
  --report /tmp/openviking-native.json
python3 -m unittest experiments.openviking.test_adapter -q
python3 -S -m experiments.openviking.exit_probe
```

The native probe intentionally reports blocked paths; exit zero means the
**observation was recorded**, not that native acceptance passed. The producer
and core exit proof work without OpenViking/SDK installed. Remove only owned lab
environments/projections and consumer wiring; canonical gardens/vaults stay
independent and rebuild through the deterministic baseline. No machine path or
credential enters the portable map.

Retain the idea of distinct directory overview/detail tiers and inspectable
memory changes. Reject coupling those generated tiers or external memory writes
to canonical ownership/review authority. Revisit with a pinned local model and
its license/artifact hash, approved Realm runtime/egress/storage profile, bounded
SDK/intake contract, a concrete consumer task, common-corpus quality/performance
and full lifecycle evidence. Review again by 2027-01-01. **Defer adoption** is the
proposed disposition; this result does not block ordinary Mindgarden.
