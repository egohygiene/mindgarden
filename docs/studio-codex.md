# Studio Codex protocol pilot

Studio's graph, search, and context pack use the local engine. The first
provider checkpoint uses a synthetic adapter and a separate Codex protocol
diagnostic. A signed-in, streaming Codex turn remains a later proof under #163.

For an embedded interactive client, the candidate is Codex App Server over
stdio behind a local Studio broker. Its JSON-RPC API supports conversation
lifecycle, streamed events, interruption, and approvals. The Codex SDK is
the simpler fit for scripted automation. Track one protocol schema per pinned
binary version. The documented WebSocket transport remains experimental.
[App Server](https://developers.openai.com/codex/app-server) ·
[Codex SDK](https://developers.openai.com/codex/sdk)

## Local protocol check

From a source checkout with Linux Bubblewrap isolation and a trusted
standalone Codex binary available:

```sh
python -S scripts/check_codex_app_server.py --expected-version 0.159.0-alpha.3
```

The probe mounts the binary and a fresh temporary working directory in a
separate mount, process, and network namespace. It uses the same configured
home path strings inside empty sandbox storage. Host home directories, garden
files, and inherited credentials stay outside. It checks `codex --version`,
generates the local JSON schema, checks the handshake declarations, receives
an `initialize` response, and sends `initialized`. The binary gets no thread,
turn, prompt, account, login, or tool requests. The diagnostic bounds elapsed
time, stdout, and admitted schema bytes, cleans up the process and temporary
files, and returns only fixed status fields, a parsed version, and a schema
checksum. Linux setup failures and unqualified platforms return a blocked result.

The audited Linux installation reported Codex CLI `0.159.0-alpha.3` with schema
SHA-256 `d862dc8a6fdcda2f386c43d246b05c5007f3bbfc16400ff3cac3780300833041`.
The release label is alpha. The result is `protocol-verified`, with
`connected: false`, `account_checked: false`, and `model_calls: 0`. The
handshake is a compatibility observation for this one binary and environment.
Additional binaries and macOS isolation need their own qualification.

## Before a live synthetic turn

1. Review the runtime permissions and egress on the actual target Mac or Linux
   host, using an isolated synthetic workspace. The local protocol probe
   deliberately blocks networking. A live check needs a separately approved
   model connection, explicit disclosure of the fictional prompt and context,
   and a reviewed provider boundary for the account and tool traffic. Use an
   explicit read boundary because Codex's read-only preset alone can still
   allow broad reads. Keep garden and account storage outside the model's file
   access. [App Server sandbox policy](https://developers.openai.com/codex/app-server#sandbox-read-access-readonlyaccess)
2. For a distributed local or open-source client, verify OpenAI's **Sign in
   with ChatGPT** registration and consent flow on the intended account.
   Eligible ChatGPT plan usage is a separate permission. The documented
   App Server integration sends the consented access token to a local child
   process for eligible Responses requests. Keep token storage and renewal in
   a supported local credential mechanism. API-key access is a separate
   setup billed through the API organization. Check actual entitlement in a
   successful synthetic turn. [Sign-in quickstart](https://developers.openai.com/siwc/quickstart) ·
   [Plan usage with App Server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server) ·
   [Preview limits](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations) ·
   [Codex authentication](https://developers.openai.com/codex/auth)
3. Demonstrate streaming, completion, interruption, and recovery from a
   disconnect. Verify expired credentials and revoked garden grants stop the
   relevant action. Confirm the exact model payload excludes denied records,
   tokens, and private paths. Report each observed result separately from the
   offline fake-provider and protocol proof before Studio reports a connection.
