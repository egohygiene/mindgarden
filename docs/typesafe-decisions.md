# Optional TypeSafe decisions: read-workflow intent

This is one bounded semantic-decision checkpoint under #40/#47, explicitly
selected by the maintainer. It supplies an executable synthetic example and
reusable Python boundary. It does not adopt the broader web/runtime architecture
or activate deferred #86–#91. Ordinary CLI commands remain explicit and unchanged.

## Selected decision and alternatives

Three useful candidates were identified: selecting a read workflow from a natural
language request; judging semantic relevance of already retrieved references; and
proposing a knowledge category during curation. The first is the lowest-impact
initial seam: paraphrases such as “where is this referenced?” mean backlinks,
while “what is connected nearby?” means graph traversal. Keyword rules are brittle,
and the choice needs no source bodies, private records or factual adjudication.

The existing CLI already has explicit commands, so it does not need a model to
parse its arguments. The integration is an application callable plus a runnable
example, intended for an independently approved future request interface. Jev
suggests only `search`, `graph` or `backlinks`; code maps them to the existing
`search_payload`, `graph_payload` and `backlinks_payload` services. The caller
supplies query/target/limits and a live `QueryContext` independently. The model
cannot choose executable code, arbitrary commands, gardens, parameters, scope,
review state, write actions or publication authority.

## Verified official contract

Read on 2026-11-08: [documentation index](https://docs.typesafe.ai/llms.txt),
[quickstart](https://docs.typesafe.ai/introduction/quickstart),
[coding agents](https://docs.typesafe.ai/introduction/coding-agents),
[building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one),
[confidence](https://docs.typesafe.ai/confidence), [SDK](https://docs.typesafe.ai/sdk),
[Python usage/retries](https://docs.typesafe.ai/sdk/python/usage),
[Choice](https://docs.typesafe.ai/primitives/choice),
[Noul](https://docs.typesafe.ai/primitives/noul), and
[companion Noul](https://docs.typesafe.ai/patterns/companion-noul).
The official Python package is **typesafe-sdk 0.7.5**, MIT, Python >=3.10;
its wheel SHA-256 is
`967a8b61494d536abb55ee3f3a2b10e81685cb6baad6ccdcab588bdc6c9b86d2`.
The actual SDK source/signatures and mocked HTTP serialization were inspected.
No API shape, model identifier or confidence field is inferred from another SDK.

One request asks a **Choice** for the workflow and a companion **Noul** for whether
any single supported workflow fits at all. Choice always selects an option,
even for an unsupported request. The application preserves the complete
per-option probabilities and Choice confidence. Noul is a probability of the
applicability statement; it has no separate confidence field. Choice confidence
summarizes probability concentration and is not an independent correctness check.
Code branches on applicability, selected-option probability and runner-up margin;
it does not count confidence as additional independent evidence.

Provisional local settings: applicability <=0.2 means unsupported; applicability
>=0.8, selected-option probability >=0.85 and top-minus-runner-up >=0.15 select a
workflow. Other cases request clarification. These are conservative starting
values, **not calibrated thresholds or measured model accuracy**. Dataclass
settings can change them explicitly after a real labeled evaluation.

## Setup and operation

Install the engine normally. Install the optional provider only when wanted:

```sh
python3 -m pip install --requirement requirements/typesafe.txt
```

`requirements/typesafe.txt` pins the official SDK separately. The core package
retains zero Python dependencies; no release tooling or default installation is
changed. Configure `TYPESAFE_API_KEY` through server-side environment settings or
a secret manager. Never put its value in requests, portable records, fixtures,
logs, browser configuration or this repository.

| Setting | Default / behavior |
| --- | --- |
| `TYPESAFE_ENABLED` | `false`; `true` or `1` explicitly enables the optional seam |
| `TYPESAFE_API_KEY` | Unconfigured; missing key produces an explicit fallback without network |
| `TYPESAFE_MODEL` | `jev-latest`, an official moving alias; the response's actual model is retained separately |
| `TYPESAFE_TIMEOUT_SECONDS` | 3; bounded to 0.1–10 seconds per HTTP operation and retry budget |
| `TYPESAFE_MAX_RETRIES` | 0; accepts at most 1; short bounded backoff, no unbounded Retry-After delay |
| Per-call `allow_hosted=True` | Required independently of environment setup; default denies outbound classification |

The adapter fixes the official `https://api.typesafe.ai` endpoint rather than
accepting a model/user-supplied destination or ambient base-URL override. It uses
the SDK's HTTP timeout and total retry budget, closes the client, and rejects a
late decision before dispatch. These are HTTP/retry limits, not an OS-level
real-time process deadline. No background retry/job/model loop is added.

Run the fixed public synthetic example from a repository checkout:

```sh
python3 examples/typesafe_workflow.py
TYPESAFE_ENABLED=true python3 examples/typesafe_workflow.py --allow-hosted
```

The first command demonstrates the disabled fallback. The second can call Jev
only when the optional SDK and server-side key are configured. It sends one fixed
public synthetic request, then invokes a selected read handler on a temporary
synthetic garden. It accepts no archive, vault or arbitrary private source input.
Actual query results never go back to Jev. Do not invoke this hosted seam inside
an offline/restricted workflow or send private request text without separate
authorization. A model judgment is never that authorization.

## Failure and logging contract

| Condition | Application outcome |
| --- | --- |
| Disabled | `disabled`; use existing explicit CLI commands; no SDK import/network |
| Missing key / missing optional SDK | `unconfigured` / `unavailable`; explicit CLI fallback |
| Hosted input not authorized | `policy-denied`; no provider call |
| Blank request / missing selected-handler query or target | Clarification; no guessed arguments |
| Ambiguous Choice or applicability | `clarify`; no handler selected |
| Clear unsupported applicability | `unsupported`; ignore even a high-probability Choice |
| Timeout, auth/rate-limit/transport failure or malformed/unknown answer | `unavailable`; fixed diagnostic, no provider exception body |
| Selected intent | Only the static read map can dispatch; existing scope, review, budgets, expiry/revocation and provenance checks still apply |

There is no existing generative-model fallback to reuse. Clarification or the
explicit CLI is appropriate here. Jev does not draft summaries, code or knowledge.
The standard `mindgarden.semantic_decision` logger records decision kind/version,
requested/resolved model, latency, selected route, probabilities, Choice
confidence, Noul value and fallback. It excludes input text, credentials, source
IDs and raw provider errors. Configure normal Python logging to consume it;
the SDK's own default logging redacts credential headers.

## Verification and next decision

- Twelve credential-free software tests cover clear/ambiguous/unsupported inputs,
  forced-choice applicability, disabled/unconfigured/policy fallbacks, malformed
  responses, deadlines, logging and real authorized handler dispatch. They pass
  on Python 3.12 and 3.13 without the optional SDK.
- Three **actual SDK + mocked transport** tests pass on Python 3.12; the separate
  Python 3.13 SDK run is recorded in the sprint receipt. These verify wire/parser
  compatibility and bounded retries, not predictions or model accuracy.
- [Sixteen labeled synthetic cases](../tests/fixtures/semantic-workflow/evaluation.json)
  cover clear workflows, ambiguity, unsupported actions/instructions and missing
  input. `python -m experiments.typesafe.evaluate` audits the dataset with
  `accuracy: null`, zero predictions and zero model calls.
- No TypeSafe credential is configured in this environment. The bounded live
  setup probe reports `unconfigured`; **zero cases were evaluated by a model**.
  A live smoke/accuracy result remains unavailable until server-side setup.

```sh
python -m unittest tests.test_semantic_workflow -q
# In the optional SDK environment:
python -m unittest experiments.typesafe.test_sdk_contract -q
python -m experiments.typesafe.evaluate
# After explicit credential setup, one synthetic case only:
TYPESAFE_ENABLED=true python -m experiments.typesafe.evaluate --live --limit 1 \
  --report /private/local/typesafe-evaluation.json
```

The live evaluator records the actual response model for each evaluated case;
failed/unconfigured calls cannot become accuracy evidence. Pin a returned model
version with `TYPESAFE_MODEL` for repeatable later evaluations; none is invented
here from the moving alias.

A second decision could score **already authorized public references** for
relevance. Add its own typed question/result and labeled fixtures, reuse the
adapter's `_call` credential/client/timeout boundary and `DecisionSettings`, then
keep selection/review policy in an application service. It must preserve Score
or Noul semantics rather than reusing Choice confidence rules. No generic agent,
plugin registry, automatic curation or cross-garden router is introduced now.

Full combined verification at the merged-main TypeSafe checkpoint: 393 tests
pass on Python 3.12 (361.764s) and Python 3.13 (350.318s), using
`python -m unittest discover -s tests -q`. These are local results; hosted CI
is recorded separately. The SDK wire tests remain outside the default suite.
