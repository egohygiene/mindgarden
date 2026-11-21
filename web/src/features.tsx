import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft, ArrowRight, BookOpen, ChevronDown, CircleAlert, Download,
  FileText, Fingerprint, GitFork, Layers, Link2, Search, ShieldCheck,
} from "lucide-react";
import { useId, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { QUERY_MAX_LENGTH, referenceKey } from "./api";
import type { GardenClient, NoteSummary, SourceCitation } from "./api";
import "./features.css";

type OpenNote = (reference: string) => void;
type SearchResult = Awaited<ReturnType<GardenClient["search"]>>["results"][number];
type SelectionReason = SearchResult["selection_reasons"][number];
type NoteDetail = Awaited<ReturnType<GardenClient["note"]>>;
type Qualifications = NoteDetail["note"]["qualifications"];
type Relation = NoteDetail["links"][number] | NoteDetail["backlinks"][number];

const queryOptions = {
  networkMode: "always",
  retry: false,
  staleTime: 0,
  gcTime: 0,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
} as const;

const fieldLabels: Record<string, string> = {
  title: "Title", heading: "Heading", headings: "Heading", tag: "Tag", tags: "Tag",
  content: "Note text", body: "Note text", domain: "Domain", topic: "Topic",
};

function label(value: string) {
  const words = value.replace(/[-_]/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function plural(count: number, noun: string) {
  return count + " " + noun + (count === 1 ? "" : "s");
}

function noteTitle(notes: readonly NoteSummary[], reference: string) {
  return notes.find((note) => referenceKey(note.reference) === reference)?.title;
}

function matchArea(reason: SelectionReason) {
  if (reason.field) return fieldLabels[reason.field] ?? label(reason.field);
  const areas = [
    reason.title && "Title",
    reason.tag && "Tag",
    reason.heading && "Heading",
    !!reason.bodyFrequency && "Note text",
  ];
  return areas.filter(Boolean).join(" · ") || "Keyword";
}

function Heading({ title, children }: { title: string; children?: ReactNode }) {
  return <header className="fv-heading">
    <h1>{title}</h1>
    {children && <div className="fv-heading-detail">{children}</div>}
  </header>;
}

function Section({ title, icon, children, className = "" }: {
  title: string; icon?: ReactNode; children: ReactNode; className?: string;
}) {
  return <section className={`panel fv-card ${className}`}>
    <h2 className="fv-card-heading">{icon}{title}</h2>
    {children}
  </section>;
}

function Feedback({ children, error = false, loading = false }: {
  children: ReactNode; error?: boolean; loading?: boolean;
}) {
  return <div className={`fv-feedback${error ? " fv-error" : ""}`}
    role={error ? "alert" : loading ? "status" : undefined}>
    {error ? <CircleAlert aria-hidden="true" size={18} /> : null}
    {children}
  </div>;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "This view could not be verified. Try again.";
}

function QueryForm({ query, context = false, onSubmit }: {
  query: string; context?: boolean; onSubmit: (query: string) => void;
}) {
  const [draft, setDraft] = useState(query);
  const field = useId();
  const Icon = context ? Layers : Search;
  const inputLabel = context ? "Topic or keywords" : "Search notes";
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(draft.trim());
  }
  return <form className="fv-query" onSubmit={submit} role={context ? undefined : "search"}
    aria-label={context ? undefined : "Search notes"}>
    <label htmlFor={field}>{inputLabel}</label>
    <div className="fv-query-row">
      <div className="fv-query-input">
        <Icon aria-hidden="true" size={18} />
        <input id={field} type="search" maxLength={QUERY_MAX_LENGTH} value={draft}
          autoComplete="off" spellCheck={false} required={context}
          placeholder={context ? "Try accessibility or household spending" : "Find notes by title, topic, or keyword"}
          onChange={(event) => setDraft(event.currentTarget.value)} />
      </div>
      <button type="submit" className="button primary">
        {context ? "Build context pack" : "Search"}<ArrowRight aria-hidden="true" size={16} />
      </button>
    </div>
  </form>;
}

function NotesRow({ note, onOpenNote }: { note: NoteSummary | SearchResult; onOpenNote: OpenNote }) {
  const heading = useId();
  const search = "selection_reasons" in note ? note : null;
  const domains = "domains" in note ? note.domains : [];
  const topics = "topics" in note ? note.topics : [];
  const sourceCount = "source_count" in note ? note.source_count : note.sources.length;
  const tags = [...new Set([...domains, ...topics])].slice(0, 3);
  return <li className="fv-note-row">
    <button type="button" className="fv-note-hit" aria-labelledby={heading}
      onClick={() => onOpenNote(referenceKey(note.reference))}>
      <span className="fv-note-icon"><FileText aria-hidden="true" size={20} /></span>
      <span className="fv-note-info">
        <strong id={heading}>{note.title}</strong>
        {search?.snippet && <span className="fv-note-snippet">{search.snippet}</span>}
        <span className="fv-note-meta">
          <span>{plural(sourceCount, "citation")}</span>
          {tags.length > 0 && <span>{tags.map(label).join(" · ")}</span>}
        </span>
      </span>
      <ArrowRight className="fv-note-arrow" aria-hidden="true" size={18} />
    </button>
    {!!search?.selection_reasons.length && <details className="fv-match">
      <summary>Why it matched <ChevronDown aria-hidden="true" size={15} /></summary>
      <ul>
        {search.selection_reasons.map((reason, index) => <li key={`${reason.term}-${index}`}>
          <strong>{matchArea(reason)}</strong> <span>{reason.term}</span> <span>+{reason.score}</span>
        </li>)}
      </ul>
    </details>}
  </li>;
}

export function NotesView({ client, notes, query, onSearch, onOpenNote, canSearch }: {
  client: GardenClient; notes: readonly NoteSummary[]; query: string; onSearch: (query: string) => void;
  onOpenNote: OpenNote; canSearch: boolean;
}) {
  const searching = canSearch && query.length > 0;
  const results = useQuery({
    ...queryOptions,
    queryKey: ["studio", "search", query],
    queryFn: ({ signal }) => client.search(query, signal),
    enabled: searching,
  });
  const items = searching ? results.data?.results ?? [] : notes;
  function search(nextQuery: string) {
    if (nextQuery && nextQuery === query) void results.refetch();
    else onSearch(nextQuery);
  }
  return <div className="fv-page">
    <Heading title="Notes"><p>Browse reviewed knowledge and follow it back to the source.</p></Heading>
    {canSearch && <QueryForm key={query} query={query} onSubmit={search} />}
    <Section title={searching ? "Search results" : "All visible notes"}
      icon={<BookOpen aria-hidden="true" size={19} />} className="fv-library">
      {searching && results.isFetching ? <Feedback loading>Searching reviewed notes…</Feedback>
        : searching && results.isError ? <Feedback error>{errorMessage(results.error)}</Feedback>
        : items.length ? <ul className="fv-note-list">{items.map((note) =>
          <NotesRow key={referenceKey(note.reference)} note={note} onOpenNote={onOpenNote} />)}</ul>
        : <Feedback>{searching ? "No reviewed notes match this search." : "This session has no reviewed notes to show."}</Feedback>}
    </Section>
  </div>;
}

function CitationIdentity({ citation }: { citation: SourceCitation }) {
  return <details className="fv-identity">
    <summary>Revision and checksum <ChevronDown aria-hidden="true" size={15} /></summary>
    <dl>
      <dt>Represented source revision</dt><dd><code>{citation.source.revision ?? "Unavailable"}</code></dd>
      <dt>Excerpt SHA-256</dt><dd><code>{citation.content_sha256}</code></dd>
    </dl>
  </details>;
}

function EvidenceBody({ client, reference, ordinal }: {
  client: GardenClient; reference: string; ordinal: number;
}) {
  const excerpt = useQuery({
    ...queryOptions,
    queryKey: ["studio", "evidence", reference, ordinal],
    queryFn: ({ signal }) => client.evidence(reference, ordinal, signal),
  });
  if (excerpt.isFetching) return <Feedback loading>Verifying the exact excerpt…</Feedback>;
  if (excerpt.isError) return <Feedback error>{errorMessage(excerpt.error)}</Feedback>;
  if (!excerpt.data) return null;
  return <div className="fv-excerpt">
    <p className="fv-excerpt-label"><Fingerprint aria-hidden="true" size={15} /> Exact source excerpt</p>
    <blockquote>{excerpt.data.text || "This selection contains no text."}</blockquote>
    <p className="fv-excerpt-trust">Untrusted source text</p>
  </div>;
}

function CitationCard({ citation, ordinal, evidence }: {
  citation: SourceCitation; ordinal: number; evidence?: { client: GardenClient; reference: string };
}) {
  const [expanded, setExpanded] = useState(false);
  const excerptId = useId();
  return <li className="fv-citation">
    <div className="fv-citation-top">
      <span className="fv-citation-icon"><FileText aria-hidden="true" size={17} /></span>
      <div>
        <p className="fv-citation-name">{citation.source.id}</p>
        <p className="fv-citation-where">{citation.source.garden} <span aria-hidden="true">·</span> <code>{citation.locator}</code></p>
      </div>
    </div>
    <CitationIdentity citation={citation} />
    {evidence && <>
      <button type="button" className="fv-disclosure-button" aria-controls={excerptId} aria-expanded={expanded}
        aria-label={`${expanded ? "Hide" : "Open"} source excerpt: ${citation.source.id}, citation ${ordinal + 1}`}
        onClick={() => setExpanded(!expanded)}>
        {expanded ? "Hide source excerpt" : "Open source excerpt"}<ChevronDown aria-hidden="true" size={16} />
      </button>
      <div id={excerptId} hidden={!expanded}>
        {expanded && <EvidenceBody {...evidence} ordinal={ordinal} />}
      </div>
    </>}
  </li>;
}

function CitationList({ citations, evidence }: {
  citations: readonly SourceCitation[]; evidence?: { client: GardenClient; reference: string };
}) {
  if (!citations.length) return <p className="fv-subtle">No source citations are visible.</p>;
  return <ul className="fv-citations">{citations.map((citation, index) => <CitationCard
    key={`${referenceKey(citation.source)}:${citation.locator}:${citation.content_sha256}:${index}`}
    citation={citation} ordinal={index} evidence={evidence} />)}</ul>;
}

function QualificationsCard({ qualifications, notes, onOpenNote }: {
  qualifications: Qualifications; notes: readonly NoteSummary[]; onOpenNote: OpenNote;
}) {
  const { attribution, epistemic_state, uncertainty, caveats, contradictions, redactions } = qualifications;
  const state = epistemic_state && epistemic_state !== "unverified" ? label(epistemic_state) : "";
  const author = attribution && attribution !== "not-declared" ? attribution : "";
  const cautions = [...uncertainty, ...caveats];
  if (!state && !author && !cautions.length && !contradictions.length && !redactions?.length) return null;
  return <Section title="Attribution and caveats" icon={<CircleAlert aria-hidden="true" size={19} />}>
    {(state || author) && <dl className="fv-annotation-meta">
      {state && <><dt>Epistemic state</dt><dd>{state}</dd></>}
      {author && <><dt>Attribution</dt><dd>{author}</dd></>}
    </dl>}
    {(cautions.length > 0 || contradictions.length > 0 || !!redactions?.length) && <ul className="fv-caveats">
      {cautions.map((caution, index) => <li key={`${index}-${caution}`}>{caution}</li>)}
      {contradictions.map((reference) => {
        const key = referenceKey(reference);
        return <li key={key}>Conflicting account in{" "}
          <button type="button" className="fv-link" onClick={() => onOpenNote(key)}>
            {noteTitle(notes, key) ?? reference.id}
          </button>
        </li>;
      })}
      {redactions?.map((redaction, index) => <li key={index}>Redaction: {redaction.rationale}</li>)}
    </ul>}
  </Section>;
}

function RelatedNotes({ title, relations, onOpenNote }: {
  title: string; relations: readonly Relation[]; onOpenNote: OpenNote;
}) {
  if (!relations.length) return null;
  return <Section title={title} icon={<Link2 aria-hidden="true" size={19} />}>
    <ul className="fv-related-list">{relations.map((relation) => {
      const key = referenceKey(relation.reference);
      return <li key={`${key}:${relation.type}`}>
        <button type="button" className="fv-related" onClick={() => onOpenNote(key)}>
          <span><strong>{relation.title}</strong><span>{label(relation.type)}</span></span>
          <ArrowRight aria-hidden="true" size={16} />
        </button>
      </li>;
    })}</ul>
  </Section>;
}

export function NoteView({ client, reference, onOpenNote, onBack, backLabel = "Back to notes", onExplore, canReadEvidence, notes = [] }: {
  client: GardenClient; reference: string; onOpenNote: OpenNote; onBack: () => void;
  backLabel?: string; onExplore?: OpenNote; canReadEvidence: boolean; notes?: readonly NoteSummary[];
}) {
  const detail = useQuery({
    ...queryOptions,
    queryKey: ["studio", "note", reference],
    queryFn: ({ signal }) => client.note(reference, signal),
  });
  const back = <button type="button" className="fv-back" onClick={onBack}>
    <ArrowLeft aria-hidden="true" size={17} /> {backLabel}
  </button>;
  if (detail.isFetching || detail.isError || !detail.data) return <div className="fv-page">
    {back}<Heading title="Note" />
    {detail.isError ? <Feedback error>{errorMessage(detail.error)}</Feedback>
      : <Feedback loading>Opening reviewed knowledge…</Feedback>}
  </div>;
  const { note, links, backlinks } = detail.data;
  return <div className="fv-page">
    <div className="fv-note-actions">
      {back}
      {onExplore && <button type="button" className="button" onClick={() => onExplore(reference)}>
        <GitFork aria-hidden="true" size={17} /> Find on map
      </button>}
    </div>
    <Heading title={note.title}>
      <ul className="fv-pills" aria-label="Note details">
        <li><ShieldCheck aria-hidden="true" size={15} /> {label(note.review.state)}</li>
        <li>{label(note.scope.visibility)}</li>
        {note.domains.map((domain) => <li key={domain}>{label(domain)}</li>)}
      </ul>
    </Heading>
    <div className="fv-note-grid">
      <div className="fv-note-column">
        <Section title={note.record_type === "claim" ? "Reviewed claim" : "Reviewed knowledge"} icon={<BookOpen aria-hidden="true" size={19} />}>
          <p className="fv-prose">{note.content}</p>
        </Section>
        <QualificationsCard qualifications={note.qualifications} notes={notes} onOpenNote={onOpenNote} />
        <RelatedNotes title="Outgoing connections" relations={links} onOpenNote={onOpenNote} />
        <RelatedNotes title="Backlinks" relations={backlinks} onOpenNote={onOpenNote} />
      </div>
      <div className="fv-note-column">
        <Section title={`Source citations (${note.sources.length})`} icon={<Fingerprint aria-hidden="true" size={19} />}>
          <CitationList key={reference} citations={note.sources} evidence={canReadEvidence ? { client, reference } : undefined} />
        </Section>
      </div>
    </div>
  </div>;
}

function downloadContext(bytes: Uint8Array) {
  const href = URL.createObjectURL(new Blob([new Uint8Array(bytes)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = href;
  link.download = "mindgarden-context.json";
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 1000);
}

export function ContextView({ client, query, onBuild, onOpenNote, notes, enabled }: {
  client: GardenClient; query: string; onBuild: (query: string) => void; onOpenNote: OpenNote;
  notes: readonly NoteSummary[]; enabled: boolean;
}) {
  const active = enabled && query.length > 0;
  const context = useQuery({
    ...queryOptions,
    queryKey: ["studio", "context", query],
    queryFn: ({ signal }) => client.context(query, signal),
    enabled: active,
  });
  const formatter = new Intl.NumberFormat();
  function build(nextQuery: string) {
    if (nextQuery && nextQuery === query) void context.refetch();
    else onBuild(nextQuery);
  }
  const loaded = active && !context.isFetching && !context.isError ? context.data : undefined;
  return <div className="fv-page">
    <Heading title="Context pack"><p>Bundle the most relevant reviewed notes with their exact citations.</p></Heading>
    {!enabled ? <Feedback>This session does not allow context packs.</Feedback>
      : <QueryForm key={query} query={query} context onSubmit={build} />}
    {active && context.isFetching && <Feedback loading>Building a bounded context pack…</Feedback>}
    {active && context.isError && <Feedback error>{errorMessage(context.error)}</Feedback>}
    {loaded && <Section title="Included notes" icon={<Layers aria-hidden="true" size={19} />}>
      <div className="fv-pack-toolbar">
        <div>
          <p>{plural(loaded.pack.included.length, "note")} · {label(loaded.pack.scope.visibility)}</p>
          <p className="fv-subtle">
            {formatter.format(loaded.bytes.byteLength)} of {formatter.format(loaded.pack.budget.max_bytes)} bytes
          </p>
        </div>
        {!!loaded.pack.included.length && <button type="button" className="button"
          onClick={() => downloadContext(loaded.bytes)}>
          <Download aria-hidden="true" size={17} /> Download JSON
        </button>}
      </div>
      {loaded.pack.included.length ? <ul className="fv-pack-list">{loaded.pack.included.map((note) => {
        const key = referenceKey(note.reference);
        return <li className="fv-pack-note" key={key}>
          <h3><button type="button" className="fv-link" onClick={() => onOpenNote(key)}>
            {noteTitle(notes, key) ?? note.reference.id}
          </button></h3>
          <p className="fv-subtle">{note.selection_reason === "lexical-query" ? "Selected by keyword match" : "Explicitly selected"}</p>
          <p className="fv-prose">{note.content}</p>
          <CitationList citations={note.sources} />
        </li>;
      })}</ul> : <Feedback>No matching reviewed notes fit this pack. Try another topic.</Feedback>}
    </Section>}
  </div>;
}
