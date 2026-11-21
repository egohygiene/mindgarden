import {
  ArrowRight, ArrowUpRight, BookOpen, BookOpenCheck, Check, ChevronDown, CircleDot, Download, FileText,
  Fingerprint, LockKeyhole, MessageSquare, ScrollText, ShieldCheck, Sparkles, Square, Wallet,
} from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { GardenApiError, QUERY_MAX_LENGTH, referenceKey } from "./api";
import type {
  AssistantCitation, AssistantInput, AssistantLens, AssistantPreview, BookletFormat, BookletMonth,
  BookletPreview, GardenClient, GardenOverview, SourceCitation,
} from "./api";
import "./assistant.css";

type ReadNote = (ref: string) => void;

const initialChat: AssistantInput = { lens: "garden", question: "", focus: null };
const bookletMonth: BookletMonth = "2026-01";

function useOperation<Kind extends string>() {
  const current = useRef<{ controller: AbortController; kind: Kind } | null>(null);
  const [busy, setBusy] = useState<Kind | null>(null);

  useEffect(() => () => current.current?.controller.abort(), []);

  function start(kind: Kind) {
    if (current.current) return null;
    const controller = new AbortController();
    current.current = { controller, kind };
    setBusy(kind);
    return controller;
  }

  function finish(controller: AbortController) {
    if (controller !== current.current?.controller) return;
    current.current = null;
    setBusy(null);
  }

  function stop() {
    const action = current.current;
    if (!action) return null;
    current.current = null;
    action.controller.abort();
    setBusy(null);
    return action.kind;
  }

  return { busy, start, finish, stop };
}

function errorText(error: unknown) {
  return error instanceof GardenApiError ? error.message : "The local request couldn't be completed. Try again.";
}

function sessionDenied(error: unknown) {
  return error instanceof GardenApiError && (error.status === 403 || [
    "WEB_ACCESS", "SESSION_EXPIRED", "SESSION_REVOKED", "SESSION_STALE", "SESSION_CONFIGURATION",
    "SESSION_REVISION", "QUERY_INTEGRITY", "PROJECTION_DENIED",
  ].includes(error.code));
}

function requestInput(input: AssistantInput): AssistantInput {
  return { ...input, question: input.question.replace(/[\r\n\t]+/g, " ").trim() };
}

function sameCitation(first: SourceCitation, second: SourceCitation) {
  return referenceKey(first.source) === referenceKey(second.source)
    && first.source.revision === second.source.revision
    && first.locator === second.locator
    && first.content_sha256 === second.content_sha256;
}

interface Answer {
  question: string;
  lens: AssistantLens;
  text: string;
  citations: AssistantCitation[];
  records: AssistantPreview["records"];
}

export function useStudioChat(client: GardenClient) {
  const operation = useOperation<"preview" | "response">();
  const [input, setInput] = useState(initialChat);
  const [preview, setPreview] = useState<AssistantPreview | null>(null);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");
  const [canceled, setCanceled] = useState(false);

  function prepare(next: AssistantInput) {
    setInput(next);
    setPreview(null);
    setError("");
    setCanceled(false);
  }

  function selectNote(reference: string) {
    prepare({ ...input, focus: reference, lens: "garden" });
  }

  function cancel(showStatus = true) {
    if (operation.stop() === "response") {
      setAnswer(null);
      setCanceled(showStatus);
    }
  }

  function clear() {
    cancel(false);
    prepare(initialChat);
    setAnswer(null);
  }

  async function getPreview() {
    const controller = operation.start("preview");
    if (!controller) return;
    const request = requestInput(input);
    setPreview(null);
    setError("");
    setCanceled(false);
    try {
      const next = await client.assistantPreview(request, controller.signal);
      controller.signal.throwIfAborted();
      if (next.lens !== request.lens || next.focus !== request.focus) {
        throw new GardenApiError("INVALID_RESPONSE", 200);
      }
      setPreview(next);
    } catch (problem) {
      if (controller.signal.aborted) return;
      if (sessionDenied(problem)) clear();
      setError(errorText(problem));
    } finally {
      operation.finish(controller);
    }
  }

  async function run() {
    if (!preview) return;
    const controller = operation.start("response");
    if (!controller) return;
    const request = requestInput(input);
    const reviewed = preview;
    setError("");
    setCanceled(false);
    setAnswer({ question: request.question, lens: request.lens, text: "", citations: [], records: reviewed.records });
    try {
      await client.assistantRun(request, reviewed.preview_sha256, (delta) => {
        controller.signal.throwIfAborted();
        if (delta.type === "text") {
          setAnswer((current) => current && { ...current, text: current.text + delta.text });
          return;
        }
        const record = reviewed.records.find((entry) => referenceKey(entry.reference) === referenceKey(delta.reference)
          && entry.reference.revision === delta.reference.revision);
        if (!record || !record.sources.some((citation) => sameCitation(citation, delta.citation))) {
          throw new GardenApiError("INVALID_RESPONSE", 200);
        }
        setAnswer((current) => {
          if (!current || current.citations.some((citation) => referenceKey(citation.reference) === referenceKey(delta.reference)
            && sameCitation(citation.citation, delta.citation))) return current;
          return { ...current, citations: [...current.citations, delta] };
        });
      }, controller.signal);
    } catch (problem) {
      if (controller.signal.aborted) return;
      setAnswer(null);
      if (sessionDenied(problem)) clear();
      if (problem instanceof GardenApiError && problem.code === "ASSISTANT_APPROVAL") setPreview(null);
      setError(errorText(problem));
    } finally {
      operation.finish(controller);
    }
  }

  return { input, preview, answer, error, canceled, busy: operation.busy, prepare, selectNote, getPreview, run, cancel, clear };
}

function saveArtifact(blob: Blob, filename: string) {
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export function useStudioBooklet(client: GardenClient) {
  const operation = useOperation<"preview" | BookletFormat>();
  const [preview, setPreview] = useState<BookletPreview | null>(null);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState("");
  const [downloaded, setDownloaded] = useState("");

  function clear() {
    operation.stop();
    setPreview(null);
    setApproved(false);
    setError("");
    setDownloaded("");
  }

  async function getPreview() {
    const controller = operation.start("preview");
    if (!controller) return;
    setPreview(null);
    setApproved(false);
    setError("");
    setDownloaded("");
    try {
      const next = await client.bookletPreview(bookletMonth, controller.signal);
      controller.signal.throwIfAborted();
      setPreview(next);
    } catch (problem) {
      if (controller.signal.aborted) return;
      if (sessionDenied(problem)) clear();
      setError(errorText(problem));
    } finally {
      operation.finish(controller);
    }
  }

  async function download(format: BookletFormat) {
    if (!preview || !approved) return;
    const controller = operation.start(format);
    if (!controller) return;
    setError("");
    setDownloaded("");
    try {
      const artifact = await client.bookletArtifact(preview, format, controller.signal);
      controller.signal.throwIfAborted();
      saveArtifact(artifact, `mindgarden-booklet-${preview.month}${format === "pdf" ? ".pdf" : "-evidence.json"}`);
      setDownloaded(format === "pdf" ? "PDF download started." : "Evidence download started.");
    } catch (problem) {
      if (controller.signal.aborted) return;
      if (sessionDenied(problem) || (problem instanceof GardenApiError && problem.code === "BOOKLET_REVIEW")) clear();
      setError(errorText(problem));
    } finally {
      operation.finish(controller);
    }
  }

  return { preview, approved, setApproved, error, downloaded, busy: operation.busy, getPreview, download, cancel: operation.stop, clear };
}

function countLabel(count: number, item: string) {
  return `${count} ${item}${count === 1 ? "" : "s"}`;
}

function FormatLabel({ value }: { value: string }) {
  return <>{value.charAt(0).toUpperCase() + value.slice(1).replace(/[-_]/g, " ")}</>;
}

function PageHeading({ title, description }: { title: string; description: string }) {
  return <header className="studio-page-heading pilot-heading">
    <div><h1>{title}</h1><p>{description}</p></div>
    <p className="pilot-badge"><CircleDot size={13} aria-hidden="true" /> Fictional local pilot</p>
  </header>;
}

function SourceDetails({ source }: { source: SourceCitation }) {
  return <div className="pilot-source">
    <code>{referenceKey(source.source)}</code>
    <p>{source.locator}{source.source.revision && <> · <code>{source.source.revision}</code></>}</p>
    <code title="Source content SHA-256">{source.content_sha256}</code>
  </div>;
}

function SourceList({ sources }: { sources: SourceCitation[] }) {
  return <ul className="pilot-source-list">
    {sources.map((source, index) => <li key={`${referenceKey(source.source)}:${source.locator}:${index}`}>
      <SourceDetails source={source} />
    </li>)}
  </ul>;
}

function ContextPreview({ preview, busy, announce }: {
  preview: AssistantPreview;
  busy: boolean;
  announce: string;
}) {
  return <section className="panel pilot-panel pilot-context" aria-label="Context preview" aria-busy={busy}>
    <div className="pilot-section-heading">
      <div className="pilot-icon"><ShieldCheck size={21} aria-hidden="true" /></div>
      <div><h2>Context preview</h2><p>
        {countLabel(preview.records.length, "reviewed note")} · {preview.context_bytes.toLocaleString()} bytes · <FormatLabel value={preview.scope.visibility} />
      </p></div>
    </div>
    <p className="pilot-sr-only" role="status">{announce}</p>
    {preview.records.length > 0 ? <ul className="pilot-preview-records">
      {preview.records.map((record) => <li key={referenceKey(record.reference)}>
        <details>
          <summary><strong>{record.title}</strong><small>{countLabel(record.sources.length, "citation")}</small><ChevronDown size={15} aria-hidden="true" /></summary>
          <p className="pilot-record-text">{record.content}</p>
          {[...record.uncertainty, ...record.caveats].map((item, index) => <p className="pilot-caveat" key={`${index}:${item}`}>{item}</p>)}
          {!!record.sources.length && <SourceList sources={record.sources} />}
        </details>
      </li>)}
    </ul> : <p className="pilot-muted">No reviewed evidence matched. The response will report that gap.</p>}
  </section>;
}

function ChatAnswer({ answer, running, onOpenNote, onOpenBooklet }: {
  answer: Answer;
  running: boolean;
  onOpenNote: ReadNote;
  onOpenBooklet?: () => void;
}) {
  return <section className="panel pilot-panel pilot-answer" aria-label="Assistant response" aria-busy={running}>
    <div className="pilot-section-heading">
      <div className="pilot-icon"><Sparkles size={21} aria-hidden="true" /></div>
      <div><h2>Assistant response</h2><p>Fictional local provider</p></div>
    </div>
    <p className="pilot-answer-question">{answer.question}</p>
    <div className="pilot-answer-body">{answer.text || "Preparing a response…"}</div>
    {!!answer.citations.length && <details className="pilot-details" open>
      <summary><Fingerprint size={16} aria-hidden="true" /> {countLabel(answer.citations.length, "source citation")} <ChevronDown size={15} aria-hidden="true" /></summary>
      <ul className="pilot-source-list">
        {answer.citations.map((event) => {
          const key = referenceKey(event.reference);
          const note = answer.records.find((record) => referenceKey(record.reference) === key);
          return <li key={`${key}:${event.citation.locator}:${event.citation.content_sha256}`}>
            <div className="pilot-citation-head">
              <strong>{note?.title || key}</strong>
              <button className="studio-text-button" type="button" disabled={running} onClick={() => onOpenNote(key)}>
                Open cited note <ArrowUpRight size={14} aria-hidden="true" />
              </button>
            </div>
            <SourceDetails source={event.citation} />
          </li>;
        })}
      </ul>
    </details>}
    {answer.lens === "finance" && !running && !!answer.citations.length && onOpenBooklet && (
      <button className="button pilot-booklet-link" type="button" onClick={onOpenBooklet}>
        <ScrollText size={17} aria-hidden="true" /> Open consultation booklet <ArrowRight size={16} aria-hidden="true" />
      </button>
    )}
  </section>;
}

export function ChatView({ garden, chat, onOpenNote, onOpenBooklet }: {
  garden: GardenOverview;
  chat: ReturnType<typeof useStudioChat>;
  onOpenNote: ReadNote;
  onOpenBooklet?: () => void;
}) {
  const questionId = useId();
  const lensId = useId();
  const scopeId = useId();
  const selected = chat.input.focus;
  const notes = garden.notes.filter((note) => chat.input.lens === "garden"
    || note.domains.includes("financial-records") || note.topics.includes("spending"));
  const unavailableFocus = selected && !notes.some((note) => referenceKey(note.reference) === selected);
  const working = chat.busy !== null;
  const running = chat.busy === "response";
  return <>
    <PageHeading title="Chat" description="Ask about a note or the permitted garden. Preview the exact context before running the fictional assistant." />
    <div className="pilot-grid">
      <div className="pilot-stack">
        <section className="panel pilot-panel" aria-label="Compose a question">
          <div className="pilot-section-heading">
            <div className="pilot-icon"><MessageSquare size={21} aria-hidden="true" /></div>
            <div><h2>Ask the garden</h2><p>Fictional local provider · Codex disconnected</p></div>
          </div>
          <form className="pilot-form" onSubmit={(event) => {
            event.preventDefault();
            if (!working && chat.input.question.trim() && !unavailableFocus) void chat.getPreview();
          }}>
            <div className="pilot-form-scope">
              <div className="pilot-field">
                <label htmlFor={lensId}>Lens</label>
                <select id={lensId} value={chat.input.lens} disabled={working} onChange={(event) => {
                  const lens = event.currentTarget.value as AssistantLens;
                  chat.prepare({ ...chat.input, lens });
                }}>
                  <option value="garden">Garden</option>
                  <option value="finance">Finance</option>
                </select>
              </div>
              <div className="pilot-field">
                <label htmlFor={scopeId}>Scope</label>
                <select id={scopeId} value={selected || ""} disabled={working} onChange={(event) =>
                  chat.prepare({ ...chat.input, focus: event.currentTarget.value || null })}>
                  <option value="">Entire permitted garden</option>
                  {unavailableFocus && <option value={selected} disabled>Selected note unavailable in this lens</option>}
                  {notes.map((note) => <option value={referenceKey(note.reference)} key={referenceKey(note.reference)}>{note.title}</option>)}
                </select>
              </div>
            </div>
            {unavailableFocus && <p className="pilot-muted">Choose a visible note for this lens or explicitly select the entire permitted garden.</p>}
            <div className="pilot-field">
              <label htmlFor={questionId}>Question</label>
              <textarea id={questionId} value={chat.input.question} disabled={working}
                placeholder="What do my reviewed notes say about spending?" rows={3} maxLength={QUERY_MAX_LENGTH}
                autoComplete="off" spellCheck={false} required onChange={(event) =>
                  chat.prepare({ ...chat.input, question: event.currentTarget.value })} />
            </div>
            <div className="pilot-buttons">
              <button className="button" type="submit" disabled={working || !chat.input.question.trim() || !!unavailableFocus}>
                {chat.busy === "preview" ? "Building preview…" : "Preview context"} <ArrowRight size={16} aria-hidden="true" />
              </button>
              {chat.preview && <button className={running ? "button" : "button primary"} type="button"
                disabled={!running && (working || !!unavailableFocus)} onClick={() => running ? chat.cancel() : void chat.run()}>
                {running ? <><Square size={13} aria-hidden="true" /> Cancel response</>
                  : <><Sparkles size={16} aria-hidden="true" /> Run fictional assistant</>}
              </button>}
              {(chat.answer || chat.preview || chat.input.question || chat.canceled) && !running && <button
                className="studio-text-button" type="button" onClick={chat.clear}>Clear chat</button>}
            </div>
          </form>
          <p className="pilot-muted pilot-tab-note"><LockKeyhole size={14} aria-hidden="true" /> This chat stays in this tab until you close or reload it.</p>
          {chat.error && <p className="pilot-message pilot-error" role="alert">{chat.error}</p>}
          {chat.canceled && <p className="pilot-message" role="status">Response canceled.</p>}
          {running && <p className="pilot-sr-only" role="status">Generating a fictional response.</p>}
          {chat.answer && !running && <p className="pilot-sr-only" role="status">Response ready.</p>}
        </section>
        {chat.answer && <ChatAnswer answer={chat.answer} running={running} onOpenNote={onOpenNote} onOpenBooklet={onOpenBooklet} />}
      </div>
      {chat.preview ? <ContextPreview preview={chat.preview} busy={running} announce="Context preview ready." /> : (
        <section className="panel pilot-panel pilot-context" aria-label="Context preview">
          <div className="pilot-section-heading">
            <div className="pilot-icon"><ShieldCheck size={21} aria-hidden="true" /></div>
            <div><h2>Context preview</h2><p>Preview to see the notes, source locations, and scope the assistant will receive.</p></div>
          </div>
        </section>
      )}
    </div>
  </>;
}

function MoneyRows({ total }: { total: BookletPreview["totals"][number] }) {
  return <div className="pilot-money">
    <div className="pilot-net">
      <Wallet size={19} aria-hidden="true" />
      <h3>Net movement</h3>
      <strong>{total.net_movement} <span>{total.currency}</span></strong>
    </div>
    <dl className="pilot-totals">
      {([["Income", total.income], ["Expenses", total.expense], ["Refunds", total.refund], ["Transfers", total.transfer], ["Uncategorized", total.uncategorized]] as const)
        .map(([label, amount]) => <div key={label}><dt>{label}</dt><dd>{amount} <span>{total.currency}</span></dd></div>)}
    </dl>
  </div>;
}

function BookletSheet({ preview }: { preview: BookletPreview }) {
  return <article className="panel pilot-panel pilot-sheet" aria-label="Booklet preview">
    <header className="pilot-sheet-header">
      <div className="pilot-icon"><BookOpenCheck size={23} aria-hidden="true" /></div>
      <p>Monthly financial movement</p>
      <h2>January 2026</h2>
      <p>{preview.period.start} to {preview.period.end} · {preview.timezone} · Fictional data</p>
    </header>
    <div className="pilot-sheet-content">
      {preview.totals.map((total) => <MoneyRows total={total} key={total.currency} />)}
      <section className="pilot-coverage">
        <h3>Account coverage</h3>
        <ul>
          {preview.coverage.map((account) => <li key={account.account}>
            <strong>{account.account}</strong><span><FormatLabel value={account.status} /></span>
            {account.observed_first && account.observed_last && <p>Observed {account.observed_first} to {account.observed_last}</p>}
            {account.missing_declared_intervals.map(({ start, end }) => <p key={`${start}:${end}`}>Declared gap {start} to {end}</p>)}
          </li>)}
        </ul>
      </section>
      {!!preview.unresolved_transactions.length && <section className="pilot-coverage">
        <h3>Unresolved transactions</h3>
        <ul>{preview.unresolved_transactions.map((ref) => <li key={ref}><code>{ref}</code></li>)}</ul>
      </section>}
      {!!preview.limitations.length && <section className="pilot-limitations">
        <h3>What the figures cover</h3>
        <ul>{preview.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
      </section>}
      {!!preview.evidence.length && <details className="pilot-details">
        <summary><Fingerprint size={17} aria-hidden="true" /> {countLabel(preview.evidence.length, "source citation")} <ChevronDown size={15} aria-hidden="true" /></summary>
        <SourceList sources={preview.evidence} />
      </details>}
    </div>
  </article>;
}

export function BookletView({ booklet }: { booklet: ReturnType<typeof useStudioBooklet> }) {
  return <>
    <PageHeading title="Consultation booklet" description="Preview the fictional monthly financial record. After review, download the PDF and exact source evidence." />
    <div className="pilot-grid pilot-booklet-grid">
      <section className="panel pilot-panel pilot-booklet-control" aria-label="Booklet controls">
        <div className="pilot-section-heading">
          <div className="pilot-icon"><ScrollText size={21} aria-hidden="true" /></div>
          <div><h2>Review and download</h2><p>January 2026 · Fictional financial records</p></div>
        </div>
        <div className="pilot-buttons">
          <button className="button" type="button" disabled={booklet.busy !== null} onClick={() => void booklet.getPreview()}>
            {booklet.busy === "preview" ? "Building preview…" : "Preview booklet"} <ArrowRight size={16} aria-hidden="true" />
          </button>
        </div>
        {booklet.preview && <div className="pilot-review">
          <p className="pilot-muted">Review the figures, coverage, and source citations before downloading.</p>
          <button className="pilot-check" type="button" aria-pressed={booklet.approved} disabled={booklet.busy !== null}
            onClick={() => booklet.setApproved(!booklet.approved)}>
            <Check size={17} aria-hidden="true" />
            Approve preview for download
          </button>
          {booklet.approved && <p className="pilot-approved"><Check size={15} aria-hidden="true" /> This preview is approved for download.</p>}
          <div className="pilot-buttons">
            <button className="button primary" type="button" disabled={!booklet.approved || booklet.busy !== null}
              onClick={() => void booklet.download("pdf")}><Download size={15} aria-hidden="true" /> Download PDF</button>
            <button className="button" type="button" disabled={!booklet.approved || booklet.busy !== null}
              onClick={() => void booklet.download("evidence")}><FileText size={15} aria-hidden="true" /> Download evidence</button>
          </div>
        </div>}
        {booklet.error && <p className="pilot-message pilot-error" role="alert">{booklet.error}</p>}
        {booklet.downloaded && <p className="pilot-message" role="status">{booklet.downloaded}</p>}
      </section>
      {booklet.preview ? <BookletSheet preview={booklet.preview} /> : (
        <section className="panel pilot-panel pilot-booklet-empty" aria-label="Booklet preview">
          <BookOpen size={30} strokeWidth={1.4} aria-hidden="true" />
          <h2>Booklet preview</h2>
          <p>Generate a preview to see the figures and evidence for January 2026.</p>
        </section>
      )}
    </div>
  </>;
}
