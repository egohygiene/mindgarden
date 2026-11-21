# Authorize ChatGPT plan use locally

Mindgarden can register with Sign in with ChatGPT for an eligible ChatGPT
account. Start from Studio's **Models** tab. Your private state directory
holds the verified registration and session.
This is the separate plan-use connection for Studio. The Codex card can
also check the account and quotas from your local Codex CLI installation.
[Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)

## Connect in Studio

From a checkout, use the same Python interpreter you use to launch Studio.
Install the optional ID-token verifier once. If you already launch Studio in a virtual
environment, activate it and start with the install command. On Homebrew,
use `"$(brew --prefix python@3.13)/bin/python3.13"` to create the
environment if `python3.13` is outside your PATH.

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python3.13 -m pip install --requirement requirements/chatgpt.txt
npm --prefix web ci
npm --prefix web run build
PYTHONPATH="$PWD/src" python3.13 -m mindgarden visit \
  --interface studio --demo --assistant providers \
  --workspace "$HOME/mindgarden-models-demo"
```

Open the full local link printed by Studio. In **Models**, choose
**Continue with ChatGPT** on the **ChatGPT plan** card. Mindgarden opens
your system browser for the official consent screen. After OpenAI returns
you to the local callback, close that tab and return to Studio. Choose
**Check connection** to load the model picker. [Run the fictional prompt](studio-model-connections.md#chatgpt-plan)

If the sign-in window is no longer needed, use **Cancel sign-in** in Studio.
Use **Continue with ChatGPT** again when the session expires. **Sign out
of ChatGPT** attempts remote revocation and removes the local tokens.
If Studio reports unconfirmed revocation, you can remove the app in
ChatGPT settings. [Account sessions and revocation](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)

Studio uses `~/.config/mindgarden/chatgpt` by default. An explicit
`--chatgpt-state-directory` selects a different local registration.

## Optional terminal controls

`chatgpt connect` also starts consent from a terminal. To check the
cached session without opening a browser or contacting OpenAI:

```sh
PYTHONPATH="$PWD/src" python3.13 -m mindgarden chatgpt status \
  --state-directory "$HOME/.config/mindgarden/chatgpt"
```

Use the same directory and replace `status` with `refresh` to renew
the session. Replace it with `disconnect` to end the renewable session
and clear the local tokens. An unconfirmed remote revocation leaves
the local session signed out. You can remove the app in ChatGPT settings
if the service was unavailable during revocation.
[Account sessions and revocation](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)

## Local ownership

- This checkpoint uses one selected account registration per explicit
  private directory. Reauthorization uses its saved registration and
  must return the same verified identity. The stored host ID identifies
  this local installation.
- A separate IPv4 loopback listener accepts the exact callback URI with
  one-use state, nonce, and PKCE S256. The authorization code stays in
  the local process. The saved profile requires an ID token verified
  against OpenAI's signing keys and the granted plan-use scope.
- The credential file is an atomic, owner-only local control outside the
  garden and Git. The provider owns token exchange, signing keys, and
  renewable sessions. Terminal summaries expose status and expiry.
- ChatGPT account eligibility, shared usage and credit access are
  controlled in ChatGPT. A verified local OAuth session is one part of
  qualification. A finished response is the next proof.
  [ChatGPT usage settings](https://chatgpt.com/settings/usage)

The tests use synthetic identity and token fixtures. Your browser consent
and first completed live response are separate local checks.
