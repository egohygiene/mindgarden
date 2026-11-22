import { Activity, Check, CircleAlert, Clipboard, Clock3, RefreshCw, TriangleAlert } from "lucide-react";
import { useId, useState } from "react";
import "./diagnostics.css";

export type DiagnosticEvent = {
  id: number;
  source: "server" | "browser";
  provider: "chatgpt" | "codex" | "gemini" | "ollama" | "studio";
  operation: "check" | "run" | "install" | "sign-in" | "cancel" | "disconnect" | "sources" | "console" | "request";
  outcome: "ok" | "attention" | "error";
  code: string;
  at_ms: number;
  duration_ms: number;
};

type Props = {
  events: readonly DiagnosticEvent[];
  serverCapacity: number;
  loading: boolean;
  error: boolean;
  onRefresh: () => void;
};

const PROVIDERS = { chatgpt: "ChatGPT plan", codex: "Codex", gemini: "Gemini", ollama: "Ollama", studio: "Studio" };
const OPERATIONS = {
  check: "Connection check", run: "Model run", install: "Model download", "sign-in": "Sign-in",
  cancel: "Cancel sign-in", disconnect: "Sign-out", sources: "Sources check", console: "Browser console", request: "Request",
};
const OUTCOMES = { ok: "OK", attention: "Needs attention", error: "Errors" };
const OUTCOME_ICONS = { ok: Check, attention: TriangleAlert, error: CircleAlert };
const SOURCES = { server: "Local server", browser: "Browser" };
const LABELS: Record<string, string> = {
  MODEL_CHECK_OK: "Connection checked",
  MODEL_CHECK_SUPERSEDED: "Connection changed during check",
  MODEL_RUN_OK: "Model run completed",
  MODEL_INSTALL_OK: "Model download completed",
  MODEL_CATALOG_EMPTY: "ChatGPT returned no available models",
  MODEL_CATALOG_NO_ENTITLEMENT: "ChatGPT plan access unavailable for this account or policy",
  MODEL_CATALOG_FORBIDDEN: "ChatGPT models request was refused",
  MODEL_CATALOG_SERVICE_UNAVAILABLE: "ChatGPT models service is unavailable",
  MODEL_CATALOG_TRANSPORT: "ChatGPT models endpoint could not be reached",
  MODEL_CATALOG_HTTP: "ChatGPT models endpoint returned an HTTP error",
  MODEL_CATALOG_RESPONSE: "ChatGPT models response could not be verified",
  MODEL_REAUTH: "Sign-in needs to be renewed",
  MODEL_NOT_CONFIGURED: "Provider setup is required",
  MODEL_UNAVAILABLE: "Provider operation unavailable",
  MODEL_QUOTA: "Provider usage limit reached",
  MODEL_INVALID: "Model selection became unavailable",
  MODEL_REVIEW: "Preview approval needs to be renewed",
  MODEL_BUSY: "Another model operation is in progress",
  CHATGPT_LOGIN_OPENING: "Opening ChatGPT consent",
  CHATGPT_LOGIN_WAITING: "Waiting for ChatGPT consent",
  CHATGPT_LOGIN_VERIFYING: "Verifying ChatGPT sign-in",
  CHATGPT_LOGIN_AUTHORIZED: "ChatGPT sign-in verified",
  CHATGPT_LOGIN_CANCELLED: "ChatGPT sign-in canceled",
  CHATGPT_LOGIN_IDLE: "ChatGPT sign-in is idle",
  CHATGPT_LOGIN_SIGNED_OUT: "Signed out of ChatGPT",
  CHATGPT_LOGIN_REVOCATION_UNCONFIRMED: "ChatGPT signed out locally, remote revocation unconfirmed",
  CHATGPT_CALLBACK_CANCELLED: "Local consent callback canceled",
  CHATGPT_CALLBACK_PROVIDER: "ChatGPT consent callback returned an error",
  CHATGPT_CALLBACK_RESPONSE: "ChatGPT consent callback could not be verified",
  CHATGPT_CALLBACK_TIMEOUT: "ChatGPT consent callback timed out",
  CHATGPT_CONSENT_DENIED: "ChatGPT consent declined",
  CHATGPT_LOGIN_UNAVAILABLE: "ChatGPT sign-in unavailable",
  CHATGPT_STATE_BUSY: "Another ChatGPT account operation is in progress",
  CHATGPT_STATE_CHANGED: "ChatGPT account state changed",
  CHATGPT_STATE_INVALID: "Local ChatGPT account state could not be verified",
  CHATGPT_STATE_UNAVAILABLE: "Local ChatGPT account state unavailable",
  CHATGPT_OAUTH_DEPENDENCY: "ChatGPT verification dependency missing",
  CHATGPT_OAUTH_IDENTITY: "ChatGPT identity could not be verified",
  CHATGPT_OAUTH_SCOPE: "ChatGPT permission could not be verified",
  CHATGPT_OAUTH_UNAVAILABLE: "ChatGPT consent service unavailable",
  CHATGPT_OWNER_MISMATCH: "ChatGPT profile belongs to a different account",
  SESSION_CONFIGURATION: "Local session configuration changed",
  SESSION_EXPIRED: "Local session expired",
  SESSION_REVISION: "Reviewed garden revision changed",
  SESSION_REVOKED: "Local session revoked",
  SESSION_STALE: "Local session needs to be refreshed",
  SESSION_UNAVAILABLE: "Local session unavailable",
  PROJECTION_DENIED: "The session does not allow this view",
  SOURCES_OK: "Source status checked",
  BROWSER_CONSOLE_WARNING: "Browser console warning",
  BROWSER_CONSOLE_ERROR: "Browser console error",
  BROWSER_RUNTIME_ERROR: "Browser runtime error",
  BROWSER_UNHANDLED_REJECTION: "Browser promise rejected",
  DIAGNOSTIC_UNAVAILABLE: "Operation could not be verified",
};
const PAGE_SIZE = 20;

function codeFor(event: DiagnosticEvent) {
  return Object.hasOwn(LABELS, event.code) ? event.code : undefined;
}

function eventTime(milliseconds: number) {
  const date = new Date(milliseconds);
  return Number.isFinite(date.getTime()) ? date.toISOString() : undefined;
}

function elapsed(milliseconds: number) {
  return milliseconds >= 1000 ? `${(milliseconds / 1000).toFixed(1)} s` : `${milliseconds} ms`;
}

function eventOutcome(event: DiagnosticEvent) {
  return event.outcome === "error" ? "Error" : OUTCOMES[event.outcome];
}

export function DiagnosticsView({ events, serverCapacity, loading, error, onRefresh }: Props) {
  const [provider, setProvider] = useState<DiagnosticEvent["provider"] | "all">("all");
  const [outcome, setOutcome] = useState<DiagnosticEvent["outcome"] | "all">("all");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [copyStatus, setCopyStatus] = useState("");
  const chartHeading = useId();
  const timelineHeading = useId();

  const matching = events.filter((event) => (provider === "all" || event.provider === provider)
    && (outcome === "all" || event.outcome === outcome)).sort((left, right) => right.at_ms - left.at_ms || right.id - left.id);
  const visible = matching.slice(0, limit);
  const timings = matching.filter((event) => event.duration_ms > 0).slice(0, 5);
  const maximum = Math.max(1, ...timings.map((event) => event.duration_ms));

  async function copyEvents() {
    const lines = visible.map((event) => {
      const code = codeFor(event);
      return [eventTime(event.at_ms) ?? "Time unavailable", SOURCES[event.source], PROVIDERS[event.provider],
        OPERATIONS[event.operation], eventOutcome(event), code ?? "Session event", `${event.duration_ms} ms`].join(" | ");
    });
    try {
      await navigator.clipboard.writeText(["Mindgarden Studio diagnostics", ...lines].join("\n"));
      setCopyStatus("Visible diagnostics copied.");
    } catch {
      setCopyStatus("Clipboard access is unavailable.");
    }
  }

  return (
    <div className="diagnostics-view">
      <header className="studio-page-heading diagnostics-heading">
        <div>
          <h1>Diagnostics</h1>
          <p>Provider checks, consent steps, and browser events from this visit.</p>
        </div>
        <button className="button" type="button" onClick={onRefresh} disabled={loading}>
          <RefreshCw size={17} aria-hidden="true" />{loading ? "Refreshing…" : "Refresh events"}
        </button>
      </header>
      {error && <p className="diagnostics-notice" role="alert">Studio couldn’t verify the current diagnostic history. Refresh to try again.</p>}
      <p className="sr-only" role="status">{loading ? "Refreshing diagnostics." : ""}</p>

      <ul className="diagnostics-metrics" aria-label="Outcomes in this visit">
        {(["ok", "attention", "error"] as const).map((kind) => {
          const Icon = OUTCOME_ICONS[kind];
          return <li className={`panel diagnostics-metric diagnostics-${kind}`} key={kind}>
            <span className="diagnostics-metric-icon"><Icon size={19} aria-hidden="true" /></span>
            <div><p>{OUTCOMES[kind]}</p><strong>{events.filter((event) => event.outcome === kind).length}</strong></div>
          </li>;
        })}
      </ul>

      <section className="panel diagnostics-chart" aria-labelledby={chartHeading}>
        <header className="diagnostics-section-header">
          <div><h2 id={chartHeading}><Activity size={21} aria-hidden="true" />Operation durations</h2>
            <p>Most recent timed events for the selected filters.</p></div>
          {timings.length > 0 && <span className="diagnostics-scale"><Clock3 size={15} aria-hidden="true" />{elapsed(maximum)} longest shown</span>}
        </header>
        {timings.length > 0 ? <ol className="diagnostics-bars">
          {timings.map((event) => <li className={`diagnostics-${event.outcome}`} key={`${event.source}/${event.id}`}>
            <div><strong>{PROVIDERS[event.provider]}</strong><span>{OPERATIONS[event.operation]} · {eventOutcome(event)}</span></div>
            <progress value={event.duration_ms} max={maximum} aria-hidden="true" />
            <span className="diagnostics-duration">{elapsed(event.duration_ms)}</span>
          </li>)}
        </ol> : <p className="diagnostics-chart-empty">No timed operations match this view.</p>}
      </section>

      <section className="panel diagnostics-timeline" aria-labelledby={timelineHeading}>
        <header className="diagnostics-section-header">
          <div><h2 id={timelineHeading}>Event timeline</h2>
            <p>{visible.length} of {matching.length} matching events{serverCapacity > 0 && ` · Up to ${serverCapacity} server events per visit`}.</p></div>
          <button className="button" type="button" disabled={!visible.length} onClick={copyEvents}>
            <Clipboard size={16} aria-hidden="true" />Copy visible events
          </button>
        </header>
        <div className="diagnostics-filters">
          <label>Provider<select value={provider} onChange={(event) => {
            setProvider(event.currentTarget.value as typeof provider);
            setLimit(PAGE_SIZE);
            setCopyStatus("");
          }}>
            <option value="all">All providers</option>
            {Object.entries(PROVIDERS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select></label>
          <label>Outcome<select value={outcome} onChange={(event) => {
            setOutcome(event.currentTarget.value as typeof outcome);
            setLimit(PAGE_SIZE);
            setCopyStatus("");
          }}>
            <option value="all">All outcomes</option>
            {Object.entries(OUTCOMES).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select></label>
        </div>
        <p className="diagnostics-feedback" role="status">{copyStatus}</p>
        {visible.length === 0 ? (
          <p className="diagnostics-empty">{loading ? "Loading events…" : events.length ? "No events match these filters." : "No events recorded yet."}</p>
        ) : <ol className="diagnostics-list">
          {visible.map((event) => {
            const code = codeFor(event);
            const time = eventTime(event.at_ms);
            const Icon = OUTCOME_ICONS[event.outcome];
            return <li className={`diagnostics-event diagnostics-${event.outcome}`} key={`${event.source}/${event.id}`}>
              <span className="diagnostics-event-icon"><Icon size={17} aria-hidden="true" /></span>
              <div className="diagnostics-event-body">
                <strong>{code ? LABELS[code] : "Session event"}</strong>
                <p>{PROVIDERS[event.provider]} · {OPERATIONS[event.operation]} · {SOURCES[event.source]}</p>
                {code && <code>{code}</code>}
              </div>
              <div className="diagnostics-event-meta">
                <span className="diagnostics-outcome">{eventOutcome(event)}</span>
                {time ? <time dateTime={time}>{time.slice(11, 19)} UTC</time> : <span>Time unavailable</span>}
                {event.duration_ms > 0 && <span>{elapsed(event.duration_ms)}</span>}
              </div>
            </li>;
          })}
        </ol>}
        {visible.length < matching.length && <button className="button diagnostics-more" type="button"
          onClick={() => setLimit((current) => current + PAGE_SIZE)}>Show older events</button>}
      </section>
    </div>
  );
}
