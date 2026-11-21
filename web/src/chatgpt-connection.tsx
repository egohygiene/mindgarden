import { ArrowUpRight, ExternalLink, LogOut, X } from "lucide-react";
import { useEffect, useEffectEvent, useRef, useState } from "react";

import { GardenApiError } from "./api";
import type { ChatGPTConnection, ChatGPTConnectionAction, GardenClient, ModelProviderStatus } from "./api";
import { useOperation } from "./assistant";

const pollInterval = 900;

function inProgress(status?: ChatGPTConnection["status"]) {
  return status === "opening" || status === "waiting";
}

const connectionMessages = {
  CHATGPT_BROWSER: "Studio could not open your system browser. Check the default browser and try again.",
  CHATGPT_CALLBACK: "Studio could not complete the local sign-in callback. Try signing in again.",
  CHATGPT_CALLBACK_TIMEOUT: "The sign-in window expired. Choose Continue with ChatGPT to try again.",
  CHATGPT_CONSENT_DENIED: "ChatGPT consent was declined. You can start a new sign-in.",
  CHATGPT_OAUTH_CLIENT: "OpenAI did not accept this Studio registration.",
  CHATGPT_OAUTH_DEPENDENCY: "The Studio Python environment needs the ChatGPT verification dependencies.",
  CHATGPT_OAUTH_SCOPE: "ChatGPT plan permission was not granted.",
  CHATGPT_OAUTH_IDENTITY: "Studio could not verify the selected ChatGPT account.",
} as const;

function failureMessage(code?: string) {
  return code && Object.hasOwn(connectionMessages, code)
    ? connectionMessages[code as keyof typeof connectionMessages]
    : "ChatGPT sign-in could not be completed. Choose Continue with ChatGPT to try again.";
}

function connectionError(error: unknown) {
  return error instanceof GardenApiError
    ? { code: error.code, message: error.message }
    : { message: "The ChatGPT connection status could not be verified." };
}

export function useChatGPTConnection(client: GardenClient, enabled: boolean, onInvalidate: () => void) {
  const operation = useOperation<ChatGPTConnectionAction>();
  const [connection, setConnection] = useState<ChatGPTConnection>();
  const [issue, setIssue] = useState<{ code?: string; message: string }>();
  const [pollFailed, setPollFailed] = useState(false);
  const [needsReauth, setNeedsReauth] = useState(false);
  const pollController = useRef<AbortController | null>(null);
  const observed = useRef<ChatGPTConnection["status"]>(undefined);
  const knownProfile = useRef(false);
  const status = connection?.status;
  const pending = inProgress(status);
  const action = operation.busy;
  const hydrating = enabled && !connection && !pollFailed;
  const invalidate = useEffectEvent(onInvalidate);

  useEffect(() => {
    if (!enabled || !status) return;
    const previous = observed.current;
    observed.current = status;
    if (previous !== status && status !== "idle" && (previous || status !== "authorized")) invalidate();
  }, [enabled, status]);

  useEffect(() => {
    if (!enabled || action || pollFailed || (status && !inProgress(status))) return;
    const controller = new AbortController();
    pollController.current = controller;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      try {
        const next = await client.chatgptConnection(controller.signal);
        if (controller.signal.aborted) return;
        receive(next);
        if (inProgress(next.status)) timer = setTimeout(() => void poll(), pollInterval);
      } catch (problem) {
        if (controller.signal.aborted) return;
        setIssue(connectionError(problem));
        setPollFailed(true);
      }
    }

    if (status) timer = setTimeout(() => void poll(), pollInterval);
    else void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
      if (pollController.current === controller) pollController.current = null;
    };
  }, [action, client, enabled, pollFailed, status]);

  async function send(action: ChatGPTConnectionAction) {
    if (!enabled) return;
    const controller = operation.start(action);
    if (!controller) return;
    pollController.current?.abort();
    setIssue(undefined);
    onInvalidate();
    try {
      const next = await client.chatgptConnectionAction(action, controller.signal);
      if (controller.signal.aborted) return;
      receive(next);
      setPollFailed(false);
    } catch (problem) {
      if (!controller.signal.aborted) setIssue(connectionError(problem));
    } finally {
      operation.finish(controller);
    }
  }

  function refreshStatus() {
    setIssue(undefined);
    setPollFailed(false);
  }

  function receive(next: ChatGPTConnection) {
    setConnection(next);
    if (next.status === "authorized" || next.status === "signed-out") {
      knownProfile.current = next.status === "authorized";
      setNeedsReauth(false);
    }
  }

  function requireSignIn(recoverProfile = false) {
    pollController.current?.abort();
    knownProfile.current ||= recoverProfile;
    setConnection({ status: "idle" });
    setNeedsReauth(knownProfile.current);
    setPollFailed(false);
    setIssue(undefined);
  }

  function confirmReady() {
    knownProfile.current = true;
    setNeedsReauth(false);
    setConnection((current) => current?.status === "authorized" ? current : { status: "idle" });
  }

  return { connection, issue, pending, action, hydrating, pollFailed, needsReauth, refreshStatus, requireSignIn, confirmReady, send };
}

export type ChatGPTSignIn = ReturnType<typeof useChatGPTConnection>;

export function ChatGPTConnectionControls({ signIn, provider, disabled }: {
  signIn: ChatGPTSignIn;
  provider: ModelProviderStatus;
  disabled: boolean;
}) {
  const { action, connection, issue, pending, pollFailed, needsReauth, refreshStatus, send } = signIn;
  const signedIn = !needsReauth && (connection?.status === "authorized" || provider.status === "ready");
  const opening = action === "connect" || connection?.status === "opening";
  const waiting = connection?.status === "waiting";
  const failed = connection?.status === "failed";
  const dependency = (issue?.code ?? connection?.code) === "CHATGPT_OAUTH_DEPENDENCY";
  const actionDisabled = disabled || action !== null;

  let status = "";
  if (action === "disconnect") status = "Signing out of ChatGPT…";
  else if (action === "cancel") status = "Canceling sign-in…";
  else if (opening) status = "Opening your browser…";
  else if (waiting) status = "Waiting for ChatGPT consent…";
  else if (connection?.status === "cancelled") status = "Sign-in canceled.";
  else if (connection?.status === "signed-out") status = "Signed out of ChatGPT.";
  else if (needsReauth) status = "Sign in again to restore ChatGPT plan access.";
  else if (signedIn) status = provider.status === "ready"
    ? "Signed in to ChatGPT."
    : "Signed in to ChatGPT. Select Check connection to see available models.";

  return <section className="models-profile-setup" aria-label="ChatGPT plan sign-in">
    {status && <p className="models-profile-status" role="status">{status}</p>}
    {issue && <p role="alert">{issue.message}</p>}
    {!issue && failed && <p role="alert">{failureMessage(connection.code)}</p>}
    {dependency && <>
      <code>python -m pip install --requirement requirements/chatgpt.txt</code>
      <p>Run this in the Python environment for Studio, restart Studio, then try signing in.</p>
    </>}
    {connection?.remote_revocation === "unconfirmed" && <p>ChatGPT could not confirm remote revocation. Review your connected apps in ChatGPT settings.</p>}
    {!signedIn && !pending && action === null && <p>Use eligible requests from your ChatGPT plan after consenting in your system browser.</p>}
    <div className="models-actions">
      {(pending || action === "connect" || action === "cancel") ? (
        <button className="button" type="button" disabled={actionDisabled} onClick={() => void send("cancel")}>
          <X size={16} aria-hidden="true" /> Cancel sign-in
        </button>
      ) : <>
        {!signedIn && <button className="button primary" type="button" data-oai-siwc-button="" disabled={actionDisabled}
          onClick={() => void send("connect")}>
          Continue with ChatGPT <ExternalLink size={16} aria-hidden="true" />
        </button>}
        {(signedIn || needsReauth) && <button className="button" type="button" disabled={actionDisabled}
          onClick={() => void send("disconnect")}>
          <LogOut size={16} aria-hidden="true" /> Sign out of ChatGPT
        </button>}
      </>}
      {pollFailed && <button className="button" type="button" disabled={actionDisabled} onClick={refreshStatus}>
        Check sign-in status
      </button>}
    </div>
    {signedIn && <a href="https://chatgpt.com/settings/usage" rel="noreferrer">
      Manage ChatGPT usage <ArrowUpRight size={14} aria-hidden="true" />
    </a>}
  </section>;
}
