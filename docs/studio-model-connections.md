# Try model connections in Studio

The **Models** view runs a bundled fictional Willow Garden consultation
scenario. It can check a local Codex account, discover Gemini models and
run the scenario through Gemini or Ollama. The installed Python engine
and the original offline Chat and Consultation booklet are available in
the same visit.

## Launch the pilot

From the combined draft branch `feature/studio-model-connections`, use
Node 24 and Python 3.12 or 3.13.

```sh
npm --prefix web ci
npm --prefix web run build
PYTHONPATH="$PWD/src" python3.13 -m mindgarden visit \
  --interface studio --demo --assistant providers \
  --workspace "$HOME/mindgarden-models-demo"
```

Use the full loopback link printed in the terminal. On the previous
Homebrew setup, use `"$(brew --prefix python@3.13)/bin/python3.13"`
if `python3.13` is outside your PATH.

## Codex account and credits

Sign in from your terminal with the official `codex login` command.
Open **Models** and choose **Check connection** in the Codex card.
The local Codex App Server reads its signed-in account using its own
credential store. For a supported ChatGPT account the check reads usage
windows, reset times and credit fields when returned. API key sign-in
uses separate API billing. The card presents reported values without
estimating a balance or exposing the account email.

The Codex card is an account and limits check. A Codex model turn needs
a qualified restricted runtime or an eligible, separately consented
Sign in with ChatGPT inference integration. The pinned App Server
protocol from the preceding draft has no verified restricted file-read
mode for Studio turns on the target Mac.
[Codex auth](https://developers.openai.com/codex/auth) ·
[Account and rate limits](https://developers.openai.com/codex/app-server#auth-endpoints) ·
[Sign in with ChatGPT](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)

## Gemini

Create a Gemini Developer API key in your Google AI Studio project.
Set `GEMINI_API_KEY` in the server process environment before starting
Studio. To enter it from a Bash or Zsh terminal without displaying it,
run the following and launch Studio from that terminal.

```sh
printf 'Gemini API key: '
IFS= read -rs GEMINI_API_KEY
printf '\n'
export GEMINI_API_KEY
```

Click **Check connection**, select Gemini and a model from the checked
inventory, and choose **Preview fixture**. Review the exact bundled text
before choosing **Authorize cloud run**. The key stays with the Python
process. Gemini quota and billing depend on the configured project.
[Create an API key](https://ai.google.dev/gemini-api/docs/api-key) ·
[Project rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

## Ollama

Install the official Ollama runtime for your OS and start it on
`127.0.0.1:11434`. For local-only use, disable Ollama cloud features
using its documented settings. If starting the daemon yourself, set
`OLLAMA_NO_CLOUD=1` in its environment:

```sh
OLLAMA_NO_CLOUD=1 ollama serve
```

Choose **Check connection** in Studio. Use an installed model, or
review and explicitly confirm a listed download. Model downloads use
the daemon's model store and may require several gigabytes. Once
downloaded, choose the model, preview the same fixture and approve
the loopback run. An initial load can take longer than later runs.
Studio allows up to two minutes for local inference and shows the
connection as loopback. The daemon's own cloud setting controls its
network behavior.
[Install Ollama](https://docs.ollama.com/quickstart) ·
[Disable cloud features](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features)

## Pilot boundaries

The same three source labels and supplied numbers go to every model.
The expected response identifies USD 2,259.76 in net movement, the
missing account, and a follow-up about the uncategorized USD -19.99.
Model answers are displayed as text for human review. They can differ
in wording or accuracy.

Model checks and inference are explicit loopback requests. Studio
offers an approval for the selected provider and model once, with a
five-minute lifetime, and keeps the status in memory for the visit.
**Stop waiting** ends the browser wait. The provider may finish its
ongoing request. Downloads use an explicit allowlisted model and
separate one-use, model-bound approval with the same five-minute lifetime.

The model broker uses the bundled fictional prompt as its sole
scenario input. It has no retrieval or Drive access. Image and video
generation need separate model capabilities and review of generated
artifacts. This checkpoint runs text models and verifies the connection
boundary. [Studio roadmap #161](https://github.com/egohygiene/mindgarden/issues/161)

Another provider can register a connection check and a bounded text
operation with the same broker. Its adapter owns credentials, requests
and response parsing. The broker owns the approved prompt, model
selection and one-use consent. Review its reported capabilities and
account metadata before adding that provider to the model picker.

## Reproduce the checks

With the production Studio build, a local Chromium and Playwright,
run the offline browser walkthrough. Add `--axe <bundle>` to include
the accessibility checks.

```sh
PYTHONPATH=src python -m unittest tests.test_model_lab \
  tests.test_studio_model_routes tests.test_studio_model_http \
  tests.test_studio_codex -q
python scripts/check_studio_model_browser.py --chromium /usr/bin/chromium
```

The browser test exercises model switching, simulated Codex usage,
Gemini approval, Ollama download approval and the local response.
The native Linux smoke used official Ollama 0.40.17 and checksum-verified
`gemma3:1b` weights in temporary storage. With Ollama cloud features
disabled, Studio discovered the model and received a response. The tiny
model reproduced the net movement and the unresolved amount but
misstated account coverage and used the word balance. Open
**Compare with approved fixture** to inspect those errors against the
input. The native install test registered the same model from an empty
inventory using verified cached blobs and a single approved pull.

The Codex protocol and simulated authenticated response tests completed
with no local account credentials. Live account usage on the target Mac
and the first authorized Gemini API response are the next checks.
