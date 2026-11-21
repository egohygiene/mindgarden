import {
  ArrowDownLeft, ArrowLeftRight, ArrowRight, ArrowUpRight, BookOpen, ChevronDown, ChevronRight,
  FileText, Network, Search, X,
} from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { QUERY_MAX_LENGTH, referenceKey } from "./api";
import type { GardenOverview, GraphEdge, NoteSummary } from "./api";
import { GardenMap } from "./graph";
import "./explorer.css";

interface ExplorerProps {
  garden: GardenOverview;
  onNote: (ref: string) => void;
  initialFocus?: string;
}

function label(value: string) {
  const words = value.replace(/[-_]/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function countLabel(count: number, noun: string) {
  return `${count} ${noun}${count === 1 ? "" : "s"}`;
}

function searchable(value: string) {
  return value.normalize("NFKD").replace(/\p{Mark}/gu, "").replace(/[-_]/g, " ").toLowerCase();
}

function references(graph: GardenOverview["graph"]) {
  const notes = new Map(graph.nodes.map((note) => [referenceKey(note.reference), note]));
  const edges = graph.edges.filter((edge) => notes.has(edge.source) && notes.has(edge.target));
  const topics = [...new Set(graph.nodes.flatMap((note) => note.topics).filter(Boolean))].sort();
  return { notes, edges, topics };
}

function directNeighbors(focus: string | undefined, notes: ReadonlyMap<string, NoteSummary>, edges: GraphEdge[]) {
  const neighbors = new Map<string, { note: NoteSummary; relations: GraphEdge[] }>();
  if (!focus) return neighbors;

  for (const edge of edges) {
    const other = edge.source === focus ? edge.target : edge.target === focus ? edge.source : null;
    if (other === null) continue;
    const neighbor = neighbors.get(other);
    const note = notes.get(other);
    if (neighbor) neighbor.relations.push(edge);
    else if (note) neighbors.set(other, { note, relations: [edge] });
  }
  return neighbors;
}

function RelationLabel({ edge, focus }: { edge: GraphEdge; focus: string }) {
  const self = edge.source === edge.target;
  const outgoing = edge.source === focus;
  const Icon = !edge.directed ? ArrowLeftRight : outgoing ? ArrowUpRight : ArrowDownLeft;
  const direction = self ? "Self-link" : !edge.directed ? "Mutual" : outgoing ? "Outgoing" : "Incoming";
  return <span className={`garden-explorer__relation${edge.type === "contradicts" ? " garden-explorer__relation--conflict" : ""}`}>
    <Icon size={12} aria-hidden="true" />
    {direction} · {label(edge.type)}
  </span>;
}

function GraphTrail({ trail, notes, onReset, onFocus }: {
  trail: string[];
  notes: ReadonlyMap<string, NoteSummary>;
  onReset: () => void;
  onFocus: (ref: string) => void;
}) {
  return (
    <nav aria-label="Graph trail" className="garden-explorer__trail">
      <ol>
        <li>
          {trail.length > 0
            ? <button type="button" onClick={onReset}><Network size={15} aria-hidden="true" />Full map</button>
            : <span aria-current="location"><Network size={15} aria-hidden="true" />Full map</span>}
        </li>
        {trail.map((ref, index) => {
          const note = notes.get(ref);
          if (!note) return null;
          return (
            <li key={ref}>
              <ChevronRight size={13} aria-hidden="true" />
              {index === trail.length - 1
                ? <span className="garden-explorer__crumb-title" aria-current="location">{note.title}</span>
                : <button className="garden-explorer__crumb-title" type="button" onClick={() => onFocus(ref)}>{note.title}</button>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function FocusRow({ note, onFocus }: { note: NoteSummary; onFocus: (ref: string) => void }) {
  return (
    <button className="garden-explorer__note" type="button" aria-label={`Focus ${note.title}`}
      onClick={() => onFocus(referenceKey(note.reference))}>
      <FileText size={17} aria-hidden="true" />
      <span>
        <strong>{note.title}</strong>
        {note.domains[0] && <small>{label(note.domains[0])}</small>}
      </span>
      <ChevronRight size={15} aria-hidden="true" />
    </button>
  );
}

function ActiveExplorer({ garden, onNote, initialFocus }: ExplorerProps) {
  const graph = garden.graph;
  const { notes, edges, topics } = useMemo(() => references(graph), [graph]);
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState("");
  const [trail, setTrail] = useState(() => initialFocus && notes.has(initialFocus) ? [initialFocus] : []);
  const searchId = useId();
  const topicId = useId();
  const inspectorId = useId();
  const searchInput = useRef<HTMLInputElement>(null);
  const topicInput = useRef<HTMLSelectElement>(null);
  const focusHeading = useRef<HTMLHeadingElement>(null);
  const visibleTrail = trail.filter((ref) => notes.has(ref));
  const focusRef = visibleTrail.at(-1);
  const focused = focusRef ? notes.get(focusRef) : undefined;
  const neighbors = useMemo(() => directNeighbors(focusRef, notes, edges), [focusRef, notes, edges]);
  const currentTopic = topics.includes(topic) ? topic : "";
  const terms = searchable(query).trim().split(/\s+/).filter(Boolean);
  const filtered = terms.length > 0 || currentTopic !== "";
  const matches = filtered ? graph.nodes.filter((note) => {
    if (currentTopic && !note.topics.includes(currentTopic)) return false;
    const fields = [note.title, ...note.topics, ...note.domains, ...note.tags];
    const text = searchable(fields.join(" "));
    return terms.every((term) => text.includes(term));
  }) : graph.nodes;
  const mapNotes = focused ? [focused, ...[...neighbors].filter(([ref]) => ref !== focusRef)
    .map(([, entry]) => entry.note)] : matches;
  const mapped = new Set(mapNotes.map((note) => referenceKey(note.reference)));
  const map = {
    nodes: mapNotes,
    edges: edges.filter((edge) => mapped.has(edge.source) && mapped.has(edge.target)
      && (!focusRef || edge.source === focusRef || edge.target === focusRef)),
  };

  useEffect(() => {
    if (focusRef) focusHeading.current?.focus();
  }, [focusRef]);

  function focusNote(ref: string) {
    if (!notes.has(ref)) return;
    setQuery("");
    setTopic("");
    setTrail((current) => {
      const visible = current.filter((key) => notes.has(key));
      const existing = visible.indexOf(ref);
      return existing >= 0 ? visible.slice(0, existing + 1) : [...visible.slice(-5), ref];
    });
  }

  function resetMap() {
    setQuery("");
    setTopic("");
    setTrail([]);
    searchInput.current?.focus();
  }

  function filterTopic(value: string) {
    setTrail([]);
    setTopic(value);
  }

  if (!graph.nodes.length) return <p className="garden-atlas__empty">There are no notes in this view.</p>;

  return (
    <div className="garden-explorer">
      <div className="garden-explorer__controls" role="search" aria-label="Find in graph">
        <div className="garden-explorer__field">
          <label htmlFor={searchId}>Find a note or topic</label>
          <div className="garden-explorer__search">
            <Search size={18} aria-hidden="true" />
            <input ref={searchInput} id={searchId} type="search" value={query}
              placeholder="Search titles, topics, and tags" maxLength={QUERY_MAX_LENGTH}
              autoComplete="off" spellCheck={false} onChange={(event) => {
                setQuery(event.currentTarget.value);
                setTrail([]);
              }} />
            {query && <button type="button" aria-label="Clear search" onClick={() => {
              setQuery("");
              searchInput.current?.focus();
            }}><X size={17} aria-hidden="true" /></button>}
          </div>
        </div>
        {!!topics.length && <div className="garden-explorer__field">
          <label htmlFor={topicId}>Topic</label>
          <div className="garden-explorer__select">
            <select ref={topicInput} id={topicId} value={currentTopic} onChange={(event) => filterTopic(event.currentTarget.value)}>
              <option value="">All topics</option>
              {topics.map((item) => <option key={item} value={item}>{label(item)}</option>)}
            </select>
            <ChevronDown size={16} aria-hidden="true" />
          </div>
        </div>}
      </div>
      <GraphTrail trail={visibleTrail} notes={notes} onReset={resetMap} onFocus={focusNote} />
      {filtered && <div className="garden-explorer__results">
        <p role="status">{countLabel(matches.length, "matching note")}</p>
        <button type="button" onClick={resetMap}>Clear filters</button>
      </div>}
      <div className="garden-explorer__columns">
        <div className="garden-explorer__chart">
          {map.nodes.length > 0
            ? <GardenMap graph={map} onNote={focusNote} focusRef={focusRef} pointAction="Focus" textAlternative={false} />
            : <div className="garden-explorer__no-matches">
                <Search size={22} aria-hidden="true" />
                <p>No notes match these filters.</p>
                <button type="button" onClick={resetMap}>Back to full map <ArrowRight size={16} aria-hidden="true" /></button>
              </div>}
        </div>
        <section className="garden-explorer__inspector" aria-labelledby={inspectorId}>
          {focused && focusRef ? <>
            <div className="garden-explorer__note-detail">
              <p className="garden-explorer__focus-label"><span aria-hidden="true" />Focused note</p>
              <h2 id={inspectorId} ref={focusHeading} tabIndex={-1}>{focused.title}</h2>
              <p className="garden-explorer__meta">{label(focused.kind)} · {label(focused.review.state)} · {countLabel(focused.source_count, "citation")}</p>
              {!!focused.topics.filter(Boolean).length && <ul className="garden-explorer__topics" aria-label="Note topics">
                {[...new Set(focused.topics.filter(Boolean))].map((item) => <li key={item}>
                  <button type="button" onClick={() => {
                    filterTopic(item);
                    topicInput.current?.focus();
                  }} aria-label={`Browse topic ${label(item)}`}>{label(item)}</button>
                </li>)}
              </ul>}
              <button className="garden-explorer__open" type="button" onClick={() => onNote(focusRef)}>
                <BookOpen size={16} aria-hidden="true" />Open note<ArrowUpRight size={15} aria-hidden="true" />
              </button>
            </div>
            <div className="garden-explorer__neighbors">
              <h3>Connected notes</h3>
              {neighbors.size ? <ul className="garden-explorer__note-list">
                {Array.from(neighbors, ([ref, entry]) => <li key={ref}>
                  {ref === focusRef ? <p className="garden-explorer__self">This note</p> : <FocusRow note={entry.note} onFocus={focusNote} />}
                  <ul className="garden-explorer__relations" aria-label="Relationships">
                    {entry.relations.map((edge) => <li key={JSON.stringify([edge.type, edge.directed, edge.source, edge.target])}>
                      <RelationLabel edge={edge} focus={focusRef} />
                    </li>)}
                  </ul>
                </li>)}
              </ul> : <p className="garden-explorer__meta">No connections are visible for this note.</p>}
            </div>
          </> : <>
            <h2 id={inspectorId}>{filtered ? "Matching notes" : "Visible notes"}</h2>
            {matches.length > 0
              ? <ul className="garden-explorer__note-list">
                  {matches.map((note) => <li key={referenceKey(note.reference)}><FocusRow note={note} onFocus={focusNote} /></li>)}
                </ul>
              : <p className="garden-explorer__meta">Try another search or topic.</p>}
          </>}
        </section>
      </div>
    </div>
  );
}

export function KnowledgeExplorer(props: ExplorerProps) {
  if (!props.garden.capabilities.graph) {
    return <p className="garden-atlas__empty">This session does not allow the graph view.</p>;
  }
  return <ActiveExplorer {...props} />;
}
