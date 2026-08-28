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
