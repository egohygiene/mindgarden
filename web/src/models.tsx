import {
  ArrowRight, Cloud, Cpu, Download, Fingerprint, HardDrive, Plug, Server, ShieldCheck, Sparkles, Square,
} from "lucide-react";
import { useEffect, useId, useState } from "react";

import { GardenApiError } from "./api";
import type {
  GardenClient, ModelInstallPreview, ModelPreview, ModelProvider, ModelProviderStatus, ModelResult, ModelsSnapshot,
} from "./api";
import { useOperation } from "./assistant";
import { ChatGPTConnectionControls, useChatGPTConnection } from "./chatgpt-connection";
import type { ChatGPTSignIn } from "./chatgpt-connection";
import "./models.css";

const providerStatus = {
  unconfigured: "Setup required",
  unchecked: "Connection unchecked",
  ready: "Connected",
  unavailable: "Unavailable",
};

type Action = `check:${ModelProvider}` | "preview" | "run" | "install-preview" | "install";
type ReviewedResult = ModelResult & { approvedPrompt: string };

function providerName(provider: ModelProviderStatus) {
  return provider.id === "chatgpt" ? "ChatGPT plan" : provider.name;
}

function statusLabel(provider: ModelProviderStatus) {
  if (provider.status === "ready") {
    if (provider.id === "codex") return "Account checked";
    if (provider.id === "chatgpt") return provider.can_run ? "Models available" : "Account checked";
  }
  return providerStatus[provider.status];
}

function errorMessage(error: unknown) {
  return error instanceof GardenApiError ? error.message : "The local provider request could not be completed.";
}

function ResetTime({ value }: { value: string | number }) {
  const date = new Date(typeof value === "number" ? value * 1000 : value);
  return Number.isNaN(date.getTime()) ? <>{value}</> : <time dateTime={date.toISOString()}>{date.toLocaleString()}</time>;
}

function UsageLimits({ limits }: { limits: NonNullable<ModelProviderStatus["limits"]> }) {
  const { credits, windows } = limits;
  if (!windows.length && !credits) return null;
  return <details className="models-limits">
    <summary>Reported usage and credits</summary>
    <ul>
      {windows.map((window, index) => <li key={`${window.label}:${index}`}>
        <div className="models-limit-heading"><strong>{window.label}</strong><span>{window.used_percent}% used</span></div>
        <progress max={100} value={window.used_percent} aria-label={`${window.label} usage`} />
        <p className="models-muted">
          {window.window_minutes != null && `${window.window_minutes} minute window`}
          {window.window_minutes != null && window.resets_at != null && " · "}
          {window.resets_at != null && <>Resets <ResetTime value={window.resets_at} /></>}
        </p>
      </li>)}
      {credits && <li>
        <strong>{credits.unlimited ? "Unlimited credits" : credits.has_credits ? "Credits available" : "No credits available"}</strong>
        {credits.balance != null && <p className="models-muted">Reported balance {credits.balance}</p>}
      </li>}
    </ul>
  </details>;
}

function ProviderCard({ provider, busy, onCheck, onStop, signIn }: {
  provider: ModelProviderStatus;
  busy: Action | null;
  onCheck: (id: ModelProvider) => void;
  onStop: () => void;
  signIn?: ChatGPTSignIn;
}) {
  const id = useId();
  const cloud = provider.disclosure === "cloud";
  const ProviderIcon = cloud ? Cloud : HardDrive;
  return <section className="panel models-provider" aria-labelledby={id}>
    <header className="models-provider-top">
      <div className="models-icon"><ProviderIcon size={22} aria-hidden="true" /></div>
      <p className={`models-status models-status-${provider.status}`}>{statusLabel(provider)}</p>
    </header>
    <h2 id={id}>{providerName(provider)}</h2>
    <p className="models-destination">{cloud ? "Cloud provider" : "Local loopback"}</p>
    <p className="models-provider-detail">{provider.detail}</p>
    {signIn && <ChatGPTConnectionControls signIn={signIn} provider={provider} disabled={busy !== null} />}
    <div className="models-actions">
      <button className="button" type="button" disabled={busy !== null || signIn?.pending || signIn?.hydrating || !!signIn?.action} onClick={() => onCheck(provider.id)}>
        <Plug size={16} aria-hidden="true" />
        {busy === `check:${provider.id}` ? "Checking connection…" : "Check connection"}
      </button>
      {busy === `check:${provider.id}` && <button className="button" type="button" onClick={onStop}>Stop waiting</button>}
    </div>
    {provider.limits && <UsageLimits limits={provider.limits} />}
  </section>;
}

export function ModelsView({ client }: { client: GardenClient }) {
  const operation = useOperation<Action>();
  const [snapshot, setSnapshot] = useState<ModelsSnapshot>();
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [providerChoice, setProviderChoice] = useState<ModelProvider | "">("");
  const [modelChoice, setModelChoice] = useState("");
  const [preview, setPreview] = useState<ModelPreview>();
  const [result, setResult] = useState<ReviewedResult>();
  const [installChoice, setInstallChoice] = useState("");
  const [installApproved, setInstallApproved] = useState<ModelInstallPreview>();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const providerSelect = useId();
  const modelSelect = useId();
  const installSelect = useId();
  const chatgpt = useChatGPTConnection(client, !!snapshot?.providers.some((item) => item.id === "chatgpt"), clearChatGPTCatalog);
  const chatgptBusy = chatgpt.pending || chatgpt.action !== null;
  const provider = snapshot?.providers.find((item) => item.id === providerChoice);
  const providerCanRun = provider?.can_run && !(provider.id === "chatgpt" && chatgptBusy);
  const selectedProviderName = provider ? providerName(provider) : undefined;
  const resultProvider = snapshot?.providers.find((item) => item.id === result?.provider);
  const model = providerCanRun ? provider.models.find((item) => item.id === modelChoice) : undefined;
  const installOptions = snapshot?.providers.find((item) => item.id === "ollama")?.downloadable ?? [];
  const installModel = installOptions.find((item) => item.id === installChoice);
  const reviewedInstall = installApproved && installModel?.id === installApproved.model;
  const busy = operation.busy;
  const working = busy !== null;

  useEffect(() => {
    const controller = new AbortController();
    client.models(controller.signal).then((next) => {
      if (!controller.signal.aborted) setSnapshot(next);
    }).catch((problem: unknown) => {
      if (!controller.signal.aborted) setError(errorMessage(problem));
    });
    return () => controller.abort();
  }, [client, loadAttempt]);

  function clearChatGPTCatalog(detail = "Check connection to see available models.") {
    setSnapshot((current) => current && {
      ...current,
      providers: current.providers.map((item) => item.id === "chatgpt"
        ? { ...item, status: "unchecked", detail, models: [], can_run: false, limits: undefined }
        : item),
    });
    clearChatGPTSelection();
  }

  function clearChatGPTSelection() {
    setPreview((current) => current?.provider === "chatgpt" ? undefined : current);
    setResult((current) => current?.provider === "chatgpt" ? undefined : current);
    if (providerChoice === "chatgpt") setModelChoice("");
  }

  function receiveProvider(next: ModelsSnapshot, id: ModelProvider) {
    const checked = next.providers.find((item) => item.id === id);
    if (!checked) throw new GardenApiError("INVALID_RESPONSE", 200);
    setSnapshot((current) => current ? {
      ...current,
      providers: current.providers.map((item) => item.id === id ? checked : item),
    } : next);
    return checked;
  }

  async function perform<Result>(
    action: Action,
    load: (signal: AbortSignal) => Promise<Result>,
    receive: (next: Result) => void,
  ) {
    const controller = operation.start(action);
    if (!controller) return;
    setError("");
    setNotice("");
    try {
      const next = await load(controller.signal);
      if (!controller.signal.aborted) receive(next);
    } catch (problem) {
      if (controller.signal.aborted) return;
      if (problem instanceof GardenApiError && (problem.status === 403 || problem.code === "WEB_ACCESS")) {
        setSnapshot(undefined);
        setPreview(undefined);
        setResult(undefined);
        setInstallApproved(undefined);
      } else if (problem instanceof GardenApiError && problem.code === "MODEL_REAUTH") {
        chatgpt.requireSignIn(true);
        clearChatGPTCatalog(problem.message);
      }
      setError(errorMessage(problem));
    } finally {
      operation.finish(controller);
    }
  }

  function check(id: ModelProvider) {
    setPreview((current) => current?.provider === id ? undefined : current);
    if (id === "ollama") setInstallApproved(undefined);
    void perform(`check:${id}`, (signal) => client.modelCheck(id, signal), (next) => {
      const checked = receiveProvider(next, id);
      if (id === "chatgpt" && checked.status === "unconfigured") {
        const wasReady = snapshot?.providers.some((item) => item.id === id && item.status === "ready");
        chatgpt.requireSignIn(wasReady);
        clearChatGPTSelection();
      } else if (id === "chatgpt" && checked.status === "ready") {
        chatgpt.confirmReady();
      }
      setNotice(`${providerName(checked)}: ${statusLabel(checked)}.`);
    });
  }

  function chooseModel(id: string) {
    setModelChoice(id);
    setPreview(undefined);
    setResult(undefined);
    setNotice("");
    setError("");
  }

  function prepare() {
    if (!provider || !model || !snapshot) return;
    setPreview(undefined);
    setResult(undefined);
    void perform("preview", (signal) => client.modelPreview(provider.id, model.id, signal), (next) => {
      if (next.provider !== provider.id || next.model !== model.id || next.disclosure !== provider.disclosure
        || next.scenario !== snapshot.scenario.id) {
        throw new GardenApiError("INVALID_RESPONSE", 200);
      }
      setPreview(next);
      setNotice("Fictional prompt ready for review.");
    });
  }

  function run() {
    if (!preview || !provider || !model || preview.provider !== provider.id || preview.model !== model.id) return;
    const approved = preview;
    setPreview(undefined);
    setResult(undefined);
    void perform("run", (signal) => client.modelRun(approved, signal), (next) => {
      if (approved.provider !== next.provider || approved.model !== next.model) throw new GardenApiError("INVALID_RESPONSE", 200);
      setResult({ ...next, approvedPrompt: approved.prompt });
      setNotice("Generated result ready for review.");
    });
  }

  function prepareInstall() {
    if (!installModel) return;
    setInstallApproved(undefined);
    void perform("install-preview", (signal) => client.modelInstallPreview(installModel.id, signal), (next) => {
      if (next.model !== installModel.id) throw new GardenApiError("INVALID_RESPONSE", 200);
      setInstallApproved(next);
    });
  }

  function install() {
    if (!installModel || !installApproved || installModel.id !== installApproved.model) return;
    const approved = installApproved;
    setInstallApproved(undefined);
    setPreview(undefined);
    void perform("install", (signal) => client.modelInstall(approved, signal), (next) => {
      const ollama = receiveProvider(next, "ollama");
      if (ollama.models.some((item) => item.id === installModel.id)) {
        setInstallChoice("");
        setNotice(`${installModel.label} is available in Ollama.`);
      } else {
        setNotice("Download request completed. Check the connection to verify the model.");
      }
    });
  }

  function stopWaiting() {
    const action = operation.stop();
    if (action === "run") {
      setNotice(provider?.disclosure === "loopback"
        ? "Stopped waiting. Ollama may still finish the local run."
        : "Stopped waiting. The provider may still finish the request and count its usage.");
    } else if (action === "install") {
      setNotice("Stopped waiting. Ollama may still finish downloading the model.");
    } else if (action) {
      setNotice("Stopped waiting for the local connection check or preview.");
    }
  }

  return <>
    <header className="studio-page-heading models-heading">
      <div>
        <h1>Models</h1>
        <p>Check a configured provider, review a fictional prompt, and authorize one run.</p>
      </div>
      <span className="models-badge"><Fingerprint size={15} aria-hidden="true" /> Fictional provider lab</span>
    </header>
    {!snapshot && !error && <p className="panel models-feedback" role="status">Loading local provider settings…</p>}
    {error && <div className="panel models-feedback models-error">
      <p role="alert">{error}</p>
      {!snapshot && <button className="button" type="button" onClick={() => {
        setError("");
        setLoadAttempt((attempt) => attempt + 1);
      }}>Reload provider settings</button>}
    </div>}
    {notice && <p className="panel models-feedback" role="status">{notice}</p>}
    {snapshot && <>
      <div className="models-grid">
        {snapshot.providers.map((item) => <ProviderCard key={item.id} provider={item} busy={busy} onCheck={check} onStop={stopWaiting}
          signIn={item.id === "chatgpt" ? chatgpt : undefined} />)}
        {!snapshot.providers.length && <p className="panel models-feedback">No providers are configured for this launch.</p>}
      </div>
      <section className="panel models-scenario" aria-label="Fictional scenario">
        <header className="models-section-heading">
          <div className="models-icon"><Cpu size={22} aria-hidden="true" /></div>
          <div><h2>{snapshot.scenario.title}</h2><p>{snapshot.scenario.description}</p></div>
        </header>
        <div className="models-fields">
          <div className="models-field">
            <label htmlFor={providerSelect}>Provider</label>
            <select id={providerSelect} value={providerChoice} disabled={working}
              onChange={(event) => {
                const chosen = snapshot.providers.find((item) => item.id === event.currentTarget.value);
                setProviderChoice(chosen?.id ?? "");
                chooseModel("");
              }}>
              <option value="">Choose a provider</option>
              {snapshot.providers.map((item) => <option key={item.id} value={item.id} disabled={!item.can_run || !item.models.length || (item.id === "chatgpt" && chatgptBusy)}>{providerName(item)}</option>)}
            </select>
          </div>
          <div className="models-field">
            <label htmlFor={modelSelect}>Model</label>
            <select id={modelSelect} value={model?.id ?? ""} disabled={working || !providerCanRun}
              onChange={(event) => chooseModel(event.currentTarget.value)}>
              <option value="">Choose a model</option>
              {providerCanRun && provider.models.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
            </select>
          </div>
        </div>
        {!snapshot.providers.some((item) => item.can_run && item.models.length > 0) &&
          <p className="models-muted models-setup">Set up a provider and check its connection to enable a fixture run.</p>}
        <div className="models-actions">
          <button className="button" type="button" disabled={working || !model} onClick={prepare}>
            {busy === "preview" ? "Preparing preview…" : "Preview fixture"} <ArrowRight size={15} aria-hidden="true" />
          </button>
          {(busy === "preview" || busy === "run") && <button className="button" type="button" onClick={stopWaiting}>
            <Square size={14} aria-hidden="true" /> Stop waiting
          </button>}
        </div>
        {busy === "run" && <p className="models-inline-status" role="status">Waiting for {selectedProviderName}…</p>}
        {preview && <section className={`models-preview models-preview-${preview.disclosure}`} aria-label="Prompt preview">
          <header><ShieldCheck size={19} aria-hidden="true" /><h3>Prompt preview</h3></header>
          <p className="models-muted">{selectedProviderName} · <code>{preview.model}</code></p>
          <pre className="models-copy">{preview.prompt}</pre>
          <div className="models-consent">
            <p>{preview.provider === "chatgpt"
              ? "This sends the exact fictional prompt above to OpenAI using your consented ChatGPT connection. The request may count against your ChatGPT plan usage."
              : preview.disclosure === "cloud"
                ? `This sends the exact fictional prompt above to ${selectedProviderName}. The provider may count the request against your account usage.`
                : "This sends the exact fictional prompt above to Ollama over the local loopback connection."}</p>
            <button className="button primary" type="button" disabled={working} onClick={run}>
              <Sparkles size={16} aria-hidden="true" /> {preview.disclosure === "cloud" ? "Authorize cloud run" : "Authorize loopback run"}
            </button>
          </div>
        </section>}
        {result && <section className="models-preview" aria-label="Model response">
          <header><Server size={19} aria-hidden="true" /><h3>Generated result for review</h3></header>
          <p className="models-muted">{resultProvider ? providerName(resultProvider) : result.provider} · <code>{result.model}</code></p>
          <pre className="models-copy">{result.text}</pre>
          <details className="models-result-prompt">
            <summary>Compare with approved fixture</summary>
            <p className="models-muted">Check the generated figures and claims against this exact fictional prompt.</p>
            <pre className="models-copy">{result.approvedPrompt}</pre>
          </details>
        </section>}
      </section>
      {installOptions.length > 0 && <section className="panel models-scenario" aria-label="Ollama model download">
        <header className="models-section-heading">
          <div className="models-icon"><Download size={21} aria-hidden="true" /></div>
          <div><h2>Ollama model download</h2><p>Choose a supported model to make it available for local runs.</p></div>
        </header>
        <div className="models-fields">
          <div className="models-field">
            <label htmlFor={installSelect}>Model to download</label>
            <select id={installSelect} value={installModel?.id ?? ""} disabled={working}
              onChange={(event) => {
                setInstallChoice(event.currentTarget.value);
                setInstallApproved(undefined);
              }}>
              <option value="">Choose an Ollama model</option>
              {installOptions.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
            </select>
          </div>
          <div className="models-install-review">
            <button className="button" type="button" disabled={working || !installModel} onClick={prepareInstall}>
              {busy === "install-preview" ? "Preparing download preview…" : "Review model download"} <ArrowRight size={16} aria-hidden="true" />
            </button>
          </div>
        </div>
        {installModel && reviewedInstall && <div className="models-consent models-install-consent">
          <p>Ollama will download <strong>{installModel.label}</strong> (<code>{installModel.id}</code>) over the network and use disk space on the machine running Ollama.</p>
          <button className="button primary" type="button" disabled={working} onClick={install}>
            <Download size={16} aria-hidden="true" /> Download {installModel.label}
          </button>
        </div>}
        {(busy === "install" || busy === "install-preview") && <div className="models-download-status">
          <p className="models-inline-status" role="status">
            {busy === "install" ? "Waiting for the Ollama model download…" : "Preparing the exact model download details…"}
          </p>
          <button className="button" type="button" onClick={stopWaiting}>
            <Square size={14} aria-hidden="true" /> {busy === "install" ? "Stop waiting for download" : "Stop waiting"}
          </button>
        </div>}
      </section>}
    </>}
  </>;
}
