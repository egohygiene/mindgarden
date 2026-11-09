# Optional evidence-bound extraction checkpoint

Refs #13, #11 and #15. The first producer is an explicitly supplied recording,
not a bundled model. `mindgarden.extraction-request/v1` selects up to 16 exact
normalized source locators, source hashes, a private fallback garden, authored
domains/topics, producer/model/prompt/schema revisions and byte limits. Existing
session source grants authorize those sources before any text reaches a producer.
The core remains useful without AI, credentials, Google or new runtime packages.

`ExtractionProducer` is the replaceable Python protocol. Its input carries the
exact source identity/message, selected text and available speaker, branch and
time metadata. Its explicit `mindgarden.extraction-output/v1` is validated before
mapping. Supporting quotations must match selected text. Structural validity
and a matching quotation do not establish a correct interpretation.

## Mapping and review

Proposed entities become proposed concept knowledge; assertions become proposed
insight knowledge containing claims. The subject and object point to those exact
new knowledge identities. Supported predicates map only to the existing synapse
vocabulary. Context, polarity, stance, temporal qualification, uncertainty and
reported contradictions survive the mapping. Source locators bind the exact
selected evidence; model/producer/prompt/schema revisions enter the curation
transformation rationale and private batch. Available attribution is retained;
an assistant suggestion cannot become an accepted user decision through this API.

Ambiguous identities and unknown predicates stay in the inspectable batch rather
than creating aliases, merging cross-source entities or adding canonical types.
The mapper never reuses an existing entity ID based on names alone. Such proposals
need explicit resolution in an authored curation plan. All produced knowledge,
claims and synapses are unreviewed, with no review authority. Their interpretation
is unverified even if a later human approves keeping the proposal.

A person can inspect/edit `curation.json`, supply explicit human review and use
the existing `gardenize --plan/--apply` digest-bound workflow. Originals are never
overwritten. Changed proposals or source bytes fail the existing integrity checks.
Applying an unchanged accepted plan remains deterministic; rerunning a model is
not assumed to reproduce its earlier text.

## Recovery and ordinary command

Success with no candidates, partial output, unsupported input, failed provider,
invalid output and not-yet-processed units have distinct states. Failure details
are fixed codes, with no raw provider exception or source text in diagnostics.
`produce_batch` exposes a checkpoint callback after each verified unit. Interrupted
callers can persist the private checkpoint and resume completed units without
replay. Exact request/config/input digests must still agree, all source evidence
is reauthorized, and outputs are validated again. Completed partial proposals are
retained rather than silently rerun; retry their interpretation through an explicit
new request. Failed/invalid units may retry. A checkpoint is untrusted proposal
data, not an authenticated claim about model accuracy or review.

```sh
mindgarden extraction --local-config /private/bindings.json \
  --scope /private/source-session.json --input /private/request.json \
  --recorded-output /private/recording.json --max-new-units 2 \
  --output-directory /private/proposals-01
```

The recording has `producer` and `outputs` (exact selected-input digest → response).
The preview exposes the digest. Repeating with `--apply --plan-digest SHA256`
creates a private create-or-verify bundle containing request, batch and optional
curation plan, with mode 0600 files and 0700 directory. It cannot target canonical
records or source vaults. `--resume /private/proposals-01/batch.json` and a new
output directory continue the same request. `--max-new-units` bounds each run.
The command deliberately wires only the offline recording adapter; providers
cannot arrive through archive instructions or arbitrary import strings.

## Ollama evaluation boundary

The official [structured-output guide](https://docs.ollama.com/capabilities/structured-outputs)
and [chat API](https://docs.ollama.com/api/chat) were read on 2026-11-08 (maintainer
timezone). The documented `/api/chat` uses `format` with a JSON schema,
`stream: false`, an explicit model and an assistant `message.content` response.
The helper embeds a self-contained schema and uses temperature zero with a bounded
generation size. The guide says cloud structured outputs are unavailable.

`ollama_extraction.py` contains only pure request/response mapping. The optional
`experiments/ollama_extraction/evaluate.py --model YOUR_LOCAL_MODEL` defaults to a
dry run. With explicit `--live` it sends only the committed synthetic page to a
loopback endpoint, disables proxy/redirects, times out after 30 seconds, caps the
response at 256 KiB and performs zero retries. It records the actual response
model and structural result. It never reads a garden, session or private source.
The one labeled input contains ambiguity and conflicting positive/negative reports;
its expected cases and authored outputs are separate from offline software tests.

No Ollama executable or operator-selected model was available here. The dry-run
wire and offline response tests pass; live model accuracy remains **unmeasured**.
No model/version recommendation or factual-accuracy threshold is invented. The
source-grant session contract is offline; connecting a networked provider to real
private evidence requires its explicit execution-policy contract. That gate is
preserved rather than treating loopback as an implicit permission exception.

A second producer can implement the same protocol/output schema and consume the
same bounded evidence input. TypeSafe remains for narrow semantic decisions;
generative extraction is a separate role. Broad model/runtime adoption, live local
model evaluation, wider media, reviewed entity resolution and consumer acceptance
remain parent scope. Proposed runtime ADRs remain proposed.
