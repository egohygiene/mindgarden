# Combined offline pipeline proof

Refs #11–#16 and #20. The selected completion stack extends the merged private
workflow; every new checkpoint remains a draft for review. This synthetic proof
does not complete #20's approved private pilot, publication or Empathy acceptance.
All proposed ADRs and unaccepted owner contracts retain their existing status.

## What the executable proves

`scripts/pipeline_completion_demo.py` first runs the existing private workflow,
then imports a synthetic v2.0.2 archive, the captured-source bundle and a page
excerpt. Unchanged overlapping messages reuse evidence. Four explicitly granted
source units produce eight authored proposals through the optional producer
contract. A one-unit checkpoint resumes with three new calls; completed units are
not replayed. Ambiguity and unknown predicates remain inspectable unresolved data.

The emitted plan is unreviewed. A separate authored human review keeps attributed,
unverified proposals, then a reviewed private move preserves the selected entry's
claims/relationships and retains the original. Local metadata discovery returns
two gardens without opening bodies or advertising them publicly. Exact selected
reads retrieve the moved entry and its original message citation. The evidence
locator remains `json:/content/0/text`, with the original `CONVERSATION.json`
selector `/messages/1` and available assistant attribution.

The JSON context pack is 4,419 bytes within an 8,192-byte ceiling. Vault export,
relocation, restore and a clean two-garden copy with generated projections removed
preserve the exact context, graph and index. The final evidence resolver returns
`Cite exact evidence; preserve uncertainty.` Source/vault originals remain intact.
No Google/model/provider service is contacted; socket, HTTP and subprocess calls
are blocked in-process. Authored outputs prove software behavior, not model accuracy.

The [committed report](../tests/fixtures/extraction/pipeline-proof.json) contains
exact source/knowledge revisions, selected-text hash, original selector, producer
pins, projection hashes, byte budget and backup checksum. It contains no physical
locations, credentials, real archives or personal data. Timings and temporary
paths are excluded from reproducibility comparisons.

## Reproduce from source

Use Python 3.12 or 3.13 and a new or empty **private directory outside a Git
checkout**. Source grants are machine-local control state. The proof preflights
that boundary before creating material; occupied workspaces and actual `.git/HEAD`
repositories are refused. It does not weaken the registry guard to support a demo.

```sh
python3 scripts/pipeline_completion_demo.py \
  --workspace /tmp/new-mindgarden-pipeline-source --require-source
```

The script requires only the existing standard-library engine and committed
synthetic fixtures. Source specifications stay private and are not runtime inputs.
No private garden, account connection, browser profile or credential is needed.

## Clean artifacts and rebuild

The source distribution explicitly includes the one synthetic captured-source ZIP;
its required membership is checked by `tests/test_distribution.py`. General ZIP
inclusion is avoided. The v2 recipe lives with fixture data rather than importing
a test module into the standalone proof.

Build/install tools remain separate from the zero-dependency runtime. A local
source/wheel build and isolated install exercise this proof again; this is package
verification, with no version change, tag, release preparation or publication.
A clean source archive can rebuild projections against the independently installed
wheel using `--require-installed`, without importing the checkout's engine.
Exact commands/results and immutable source pins are recorded in the sprint
ledger and CONTINUITY.md after verification.

## Review boundaries

The capture wire depends on proposed Mindcap #42 at `7ee766c`; hashes do not
establish producer authenticity or human authority. Full incremental capture and
owner adoption remain open. Ollama has pure documented wire helpers and a synthetic
opt-in probe; no local model was configured, so actual accuracy is unmeasured.
Private source grants remain offline. Local organization scope uses the draft
policy; mixed private/internal output requires unavailable confidential assurance.
Remote federation, signing, installation and Aether/Akashic acceptance are unclaimed.

The same accepted curation plan applies deterministically. A new model run may
produce different proposals and requires new review. The proof does not process
real financial/legal material, approve facts, or grant publication authority.
