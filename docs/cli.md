# CLI and library contract

Mindgarden 0.x exposes one installable `mindgarden` command and a small public
Python library. Consumers pass their repository explicitly; the installed
package never becomes the owner of consumer `.garden/` knowledge.

## Installation

Install a reviewed local checkout:

```bash
python3 -m pip install "/path/to/mindgarden"
mindgarden --version
```

The package requires Python 3.12 or 3.13 and has no runtime Python
dependencies. PyPI trusted publication is reserved for the final release gate.

## Commands

```text
mindgarden validate
mindgarden init
mindgarden migrate
mindgarden ingest
mindgarden index
mindgarden search
mindgarden context
mindgarden llms
mindgarden federation build
mindgarden federation catalog
mindgarden publish project
mindgarden publish verify
mindgarden site build
mindgarden site serve
mindgarden verify
mindgarden version
mindgarden --version
```

Every garden operation accepts the long-form
`--repository-root "/path/to/consumer"` argument. Run any command with
`--help` for its complete long-form options.

Examples:

```bash
mindgarden init \
  --repository-root "/path/to/consumer" \
  --visibility "public"

mindgarden migrate \
  --repository-root "/path/to/consumer" \
  --plan

mindgarden index \
  --repository-root "/path/to/consumer" \
  --write

mindgarden search \
  --repository-root "/path/to/consumer" \
  --query "architecture decisions" \
  --limit 5

mindgarden context \
  --repository-root "/path/to/consumer" \
  --pack "example-agent-default" \
  --format "markdown"

mindgarden publish verify \
  --repository-root "/path/to/consumer"

mindgarden site serve \
  --repository-root "/path/to/consumer" \
  --port 8080
```

Ingestion remains a read-only plan unless `--write` is supplied. Public-garden
writes additionally require `--confirm-public`.

Initialization defaults to a complete read-only file plan. Migration requires
one explicit mode: `--plan`, `--apply`, or `--check`. Both apply paths require
the exact `--plan-digest` from the reviewed plan. See
[`initialization-migration.md`](initialization-migration.md) for the atomicity,
idempotency, rollback, and v0 → v1 evidence-preservation contract.

## Stable exit codes

| Code | Meaning |
| --- | --- |
| `0` | Command completed successfully. |
| `2` | Command usage or argument parsing failed. |
| `3` | A Mindgarden contract, validation, or structured-data error occurred. |
| `4` | A filesystem, encoding, or other I/O operation failed. |
| `5` | A required external adapter command failed. |

Diagnostics are written to standard error and begin with a stable Mindgarden
error category.

The additive [federation checkpoint](federation.md) uses explicit
`--local-config`, `--scope`, `--profile` and `--output-directory` inputs for
`federation build`. Its default is a read-only plan; `--apply` requires the exact
`--plan-digest`, and `--check` verifies the immutable output. `federation catalog`
accepts a machine-local `--input` request containing supplied public directories
and expected revisions. A partial catalog prints its structured result and exits
`3`; it never fetches remote gardens. Existing v0 commands remain unchanged.

## Python library

The top-level package exposes the supported 0.x library surface without
spawning the command line:

```python
from pathlib import Path

import mindgarden

repository = Path("/path/to/consumer")
note_count = mindgarden.validate_repository(repository)
index = mindgarden.build_index(repository)
```

Lower-level modules make the architectural boundary explicit:

- `mindgarden.domain.validation` owns contract parsing and validation;
- `mindgarden.application.agent` owns deterministic use cases;
- `mindgarden.application.lifecycle` owns review-gated initialization and
  migration;
- `mindgarden.adapters.publishing` and `mindgarden.adapters.quartz` own
  replaceable external projections;
- `mindgarden.interfaces.cli` owns command parsing, diagnostics, and exit codes.

## 0.x script compatibility

The extracted script paths remain thin shims during the 0.x transition:

```bash
python3 scripts/validate_garden.py \
  --repository-root "/path/to/consumer"

python3 scripts/garden_agent.py \
  --repository-root "/path/to/consumer" \
  verify

python3 scripts/publish_garden.py \
  --repository-root "/path/to/consumer" \
  verify
```

New consumers should use `mindgarden`. The compatibility shims contain no
independent implementation and will not become a second public API.

## General v1 validation

`mindgarden validate --repository-root "/path/to/workspace"` detects the selected
v0 or v1 manifest. `--format "json"` emits stable diagnostic codes, severity,
portable locations and remediation. `invalid` and `incomplete` both return the
contract exit code 3; missing cross-garden authorization is incomplete rather
than successful validation. Validation never discovers private overlays or
fetches remote schemas.

V1 checks the shipped schema vocabulary, unique identities, typed references,
immutable revisions, content/evidence/provenance hashes and supersession cycles.
Initialization and migration use the same general validator for their staged
trees. The published runtime remains dependency-free.

V1 source ingestion requires explicit local vault bindings and a reviewed plan
digest. The [archive compatibility checkpoint](conversation-archive-compatibility.md)
documents `--adapter conversation-archive --manifest-version 3.2.3`, the tested
versions/profiles, bounded validation, and compatibility gaps. See also the
[text adapter](source-adapters.md), [curation](curation-plans.md), and
[retrieval/context](v1-retrieval.md) command examples.

The [finite private-garden proof](private-garden-evidence.md) exercises the normal
CLI end to end. `mindgarden evidence` resolves exact reviewed citations; `vault
export`, `vault restore` and `vault relocate` use digest-bound plans. See
[source-vault.md](source-vault.md) for bounds, failure states and recovery.
