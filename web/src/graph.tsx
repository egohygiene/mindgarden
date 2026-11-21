import { Box, Network, Plus, Share2 } from "lucide-react";
import { Component, lazy, Suspense, useCallback, useId, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { referenceKey } from "./api";
import type { GardenOverview as Garden, GraphEdge, NoteSummary } from "./api";
import "./graph.css";

const GraphScene = lazy(() => import("./graph-scene"));

const PALETTE = {
  default: "#a7c9a5",
  focus: "#d8f596",
  business: "#b4d688",
  career: "#b7adeb",
  finance: "#e6c19a",
  household: "#88d3b8",
};

export interface PlottedNote {
  ref: string;
  title: string;
  label: string;
  color: string;
  x: number;
  y: number;
  z: number;
  focus: boolean;
}

export interface PlottedConnection {
  source: PlottedNote;
  target: PlottedNote;
  edge: GraphEdge;
}

interface Props {
  garden: Garden;
  onNote: (ref: string) => void;
  compact?: boolean;
}

function noteLabel(title: string, compact: boolean): string {
  if (!compact && title.length <= 35) return title;
  const label = title.replace(/^(Fictional|Synthetic)\s+/i, "");
  const words = label.split(/\s+/);
  const short = words.slice(0, 3).join(" ").slice(0, 30);
  return short.replace(/^./, (letter) => letter.toUpperCase()) + (short === label ? "" : "…");
}

function noteColor(domains: string[], focus: boolean): string {
  if (focus) return PALETTE.focus;
  const domain = domains[0]?.toLowerCase();
  if (domain === "business") return PALETTE.business;
  if (domain === "career") return PALETTE.career;
  if (domain === "finance" || domain === "financial") return PALETTE.finance;
  if (domain === "household") return PALETTE.household;
  return PALETTE.default;
}

function plotGraph(notes: NoteSummary[], edges: GraphEdge[], compact: boolean) {
  const degrees = new Map<string, number>();
  for (const edge of edges) {
    degrees.set(edge.source, (degrees.get(edge.source) ?? 0) + 1);
    degrees.set(edge.target, (degrees.get(edge.target) ?? 0) + 1);
  }
  const sorted = notes.map((note) => {
    const ref = referenceKey(note.reference);
    return { note, ref, degree: degrees.get(ref) ?? 0 };
  }).sort((first, second) => second.degree - first.degree);
  const visible = sorted.slice(0, compact ? 7 : 13);
  const points = visible.map(({ ref, note }, index): PlottedNote => {
    const focus = index === 0;
    const angle = -Math.PI * 0.73 + (index - 1) * (2 * Math.PI) / Math.max(1, visible.length - 1);
    const radius = index % 2 === 0 ? 1 : 0.86;
    return {
      ref,
      title: note.title,
      label: noteLabel(note.title, compact),
      color: noteColor(note.domains, focus),
      x: focus ? 360 : 360 + Math.cos(angle) * 242 * radius,
      y: focus ? 169 : 169 + Math.sin(angle) * 112 * radius,
      z: focus ? 0.75 : Math.sin(angle * 1.4) * 1.3,
      focus,
    };
  });
  const pointMap = new Map(points.map((point) => [point.ref, point]));
  const connections = edges.flatMap((edge): PlottedConnection[] => {
    const source = pointMap.get(edge.source);
    const target = pointMap.get(edge.target);
    return source && target ? [{ source, target, edge }] : [];
  });
  return { points, connections };
}

class SceneBoundary extends Component<{ onUnavailable: () => void; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch() {
    this.props.onUnavailable();
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}

function FlatGraph({ points, connections, onNote, compact }: {
  points: PlottedNote[];
  connections: PlottedConnection[];
  onNote: Props["onNote"];
  compact: boolean;
}) {
  const id = useId();
  return (
    <svg className="garden-atlas__svg" viewBox="0 0 720 360" role="group" aria-label="Interactive map of visible notes">
      <defs>
        <pattern id={id + "-grid"} width="26" height="26" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1" fill="#c6d8af" fillOpacity="0.22" />
        </pattern>
        <radialGradient id={id + "-light"}>
          <stop stopColor="#7cad54" stopOpacity="0.16" />
          <stop offset="1" stopColor="#7cad54" stopOpacity="0" />
        </radialGradient>
        <marker id={id + "-arrow"} viewBox="0 0 10 10" refX="25" refY="5" markerWidth="8" markerHeight="8" orient="auto">
          <path d="M1 1l7 4-7 4" fill="none" stroke="#baccae" strokeWidth="1.3" />
        </marker>
      </defs>
      <g aria-hidden="true" pointerEvents="none">
        <rect width="720" height="360" fill={`url(#${id}-grid)`} />
        <ellipse cx="360" cy="170" rx="323" ry="154" fill={`url(#${id}-light)`} />
        {[76, 126, 189, 253].map((radius) => (
          <ellipse key={radius} cx="360" cy="169" rx={radius} ry={radius * 0.52} className="garden-atlas__orbit" />
        ))}
        <path d="M360 22v293M78 169h564" className="garden-atlas__orbit" />
      </g>
      <g aria-hidden="true" pointerEvents="none">
        {connections.map(({ source, target, edge }) => (
          <line
            key={JSON.stringify([edge.type, edge.source, edge.target, edge.directed])}
            className={edge.type === "contradicts" ? "garden-atlas__edge garden-atlas__edge--conflict" : "garden-atlas__edge"}
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            markerEnd={edge.directed ? `url(#${id}-arrow)` : undefined}
          />
        ))}
      </g>
      {points.map(({ ref, title, label, color, x, y, focus }, index) => (
        <g
          key={ref}
          className={focus ? "garden-atlas__node garden-atlas__node--focus" : "garden-atlas__node"}
          role="button"
          aria-label={`Open ${title}`}
          tabIndex={0}
          transform={`translate(${x} ${y})`}
          onClick={() => onNote(ref)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              onNote(ref);
            }
          }}
        >
          <title>{title}</title>
          <circle r={31} fill="transparent" />
          <circle r={focus ? 30 : 21} fill={color} fillOpacity="0.10" className="garden-atlas__halo" />
          <circle r={focus ? 21 : 14} stroke={color} strokeOpacity="0.56" fill="none" />
          <circle r={focus ? 9 : 6} fill={color} className="garden-atlas__dot" />
          {index < 8 && (
            <text y={focus ? 53 : 37} className={compact ? "garden-atlas__label garden-atlas__label--compact" : "garden-atlas__label"}>
              {label}
            </text>
          )}
        </g>
      ))}
    </svg>
  );
}

function RelationshipList({ notes, edges, compact, onNote }: {
  notes: NoteSummary[];
  edges: GraphEdge[];
  compact: boolean;
  onNote: Props["onNote"];
}) {
  const noteMap = new Map(notes.map((note) => [referenceKey(note.reference), note]));
  const grouped = new Map<string, GraphEdge[]>();
  for (const edge of edges) {
    const prior = grouped.get(edge.source) ?? [];
    prior.push(edge);
    grouped.set(edge.source, prior);
  }
  return (
    <details className="garden-atlas__details" open={!compact}>
      <summary>
        <Share2 size={16} aria-hidden="true" />
        Browse notes and relationships
        <Plus className="garden-atlas__details-icon" size={16} aria-hidden="true" />
      </summary>
      <ul className="garden-atlas__relationships">
        {notes.map((note) => {
          const key = referenceKey(note.reference);
          return (
            <li key={key}>
              <button className="garden-atlas__note-link" type="button" onClick={() => onNote(key)}>{note.title}</button>
              {!!grouped.get(key)?.length && (
                <ul className="garden-atlas__links">
                  {grouped.get(key)?.map((edge) => (
                    <li key={JSON.stringify([edge.type, edge.target, edge.directed])}>
                      <span>
                        <span className="garden-atlas__sr-only">{edge.directed ? "Outgoing link: " : "Mutual link: "}</span>
                        <span aria-hidden="true">{edge.directed ? "→ " : "↔ "}</span>
                        {edge.type.replace(/[-_]/g, " ")}
                      </span>
                      <button className="garden-atlas__note-link" type="button" onClick={() => onNote(edge.target)}>
                        {noteMap.get(edge.target)?.title}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

function ActiveGraph({ garden, onNote, compact = false }: Props) {
  const { graph } = garden;
  const mapId = useId();
  const [mode, setMode] = useState<"flat" | "spatial" | "unavailable">("flat");
  const [hovered, setHovered] = useState<PlottedNote | null>(null);
  const unavailable = useCallback(() => setMode("unavailable"), []);
  const edges = useMemo(() => {
    const keys = new Set(graph.nodes.map((note) => referenceKey(note.reference)));
    return graph.edges.filter((edge) => keys.has(edge.source) && keys.has(edge.target));
  }, [graph]);
  const { points, connections } = useMemo(() => plotGraph(graph.nodes, edges, compact), [graph.nodes, edges, compact]);
  const spatial = mode === "spatial";

  if (!points.length) return <p className="garden-atlas__empty">There are no notes in this view.</p>;

  function toggleMode() {
    if (mode === "unavailable") return;
    setHovered(null);
    if (spatial) {
      setMode("flat");
      return;
    }
    try {
      const probe = document.createElement("canvas").getContext("webgl2");
      if (probe) {
        probe.getExtension("WEBGL_lose_context")?.loseContext();
        setMode("spatial");
        return;
      }
    } catch {
      // Depending on the browser, WebGL may be denied with an exception.
    }
    unavailable();
  }

  return (
    <div className={compact ? "garden-atlas garden-atlas--compact" : "garden-atlas"}>
      <div className="garden-atlas__map" id={mapId}>
        {spatial ? (
          <SceneBoundary onUnavailable={unavailable}>
            <Suspense fallback={<p className="garden-atlas__loading" role="status">Loading 3D map…</p>}>
              <GraphScene points={points} connections={connections} onNote={onNote} onHover={setHovered} onUnavailable={unavailable} />
            </Suspense>
          </SceneBoundary>
        ) : (
          <FlatGraph points={points} connections={connections} compact={compact} onNote={onNote} />
        )}
        {spatial && hovered && <div className="garden-atlas__hover">{hovered.title}</div>}
      </div>
      <div className="garden-atlas__toolbar">
        <p className="garden-atlas__hint" role="status">
          {mode === "unavailable" ? "3D is unavailable on this device. The 2D map is ready." : (
            <>
              <span className="garden-atlas__marker" aria-hidden="true" />
              {spatial ? "Drag to orbit. Select a point to open its note." : `${points.length} plotted ${points.length === 1 ? "note" : "notes"} · Select a point to open it.`}
            </>
          )}
        </p>
        <button className="garden-atlas__mode" type="button" onClick={toggleMode} aria-controls={mapId} aria-disabled={mode === "unavailable"}>
          {spatial ? <Network size={17} aria-hidden="true" /> : <Box size={17} aria-hidden="true" />}
          {spatial ? "Back to 2D" : "Explore in 3D"}
        </button>
      </div>
      <RelationshipList notes={graph.nodes} edges={edges} compact={compact} onNote={onNote} />
    </div>
  );
}

export function GardenGraph(props: Props) {
  if (!props.garden.capabilities.graph) {
    return <p className="garden-atlas__empty">This session does not allow the graph view.</p>;
  }
  return <ActiveGraph {...props} />;
}
