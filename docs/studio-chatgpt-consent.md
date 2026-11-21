# Authorize ChatGPT plan use locally

Mindgarden can register with Sign in with ChatGPT for an eligible ChatGPT
account. The command opens your browser for account selection and consent.
Your configured state directory holds the verified registration and session.
This is the separate plan-use connection for Studio. The Codex card can
also check the account and quotas from your local Codex CLI installation.
[Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)

## Connect on your Mac

From a checkout, use the same Python interpreter you use to launch Studio.
Install the optional ID-token verifier and choose a private state directory
under your home directory.

```sh
python3.13 -m pip install --requirement requirements/chatgpt.txt
PYTHONPATH="$PWD/src" python3.13 -m mindgarden chatgpt connect \
  --state-directory "$HOME/.config/mindgarden/chatgpt"
```

Use your virtual environment if your Homebrew Python manages its own
packages. Follow the browser's authorization form and review the plan-use
permission it requests. The terminal returns a brief status after it
verifies the result. To check the cached session without opening a browser
or contacting OpenAI:

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

The first draft tests browser callback, registration, refresh and local
sign-out with synthetic identity and token fixtures. It does not open an
actual account or run inference. The dependent Models draft uses this
explicit profile to list models and run the existing fictional prompt.
