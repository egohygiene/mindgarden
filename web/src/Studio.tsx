import * as Dialog from "@radix-ui/react-dialog";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  BriefcaseBusiness,
  CircleDot,
  Compass,
  GitFork,
  House,
  Layers3,
  Link2,
  Search,
  Sprout,
  Wallet,
  X,
} from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  QUERY_MAX_LENGTH,
  type GardenClient,
  type GardenOverview,
  type NoteSummary,
  referenceKey,
} from "./api";
import { ContextView, NotesView, NoteView } from "./features";
import { GardenGraph } from "./graph";

type Route =
  | { name: "overview" }
  | { name: "notes"; query: string }
  | { name: "connections" }
  | { name: "context"; query: string }
  | { name: "note"; reference: string };

const sections = [
  { label: "Overview", route: { name: "overview" }, icon: Compass },
  { label: "Library", route: { name: "notes", query: "" }, icon: BookOpen },
  { label: "Connections", route: { name: "connections" }, icon: GitFork },
  { label: "Context packs", route: { name: "context", query: "" }, icon: Layers3 },
] satisfies Array<{ label: string; route: Route; icon: typeof Compass }>;

const affiliated = [
  ["Civics", "https://civics.egohygiene.io/"],
  ["Ethics", "https://ethics.egohygiene.io/"],
  ["Akashic", "https://akashic.egohygiene.io/"],
];

function canOpen(route: Route, garden?: GardenOverview) {
  if (route.name === "connections") return garden?.capabilities.graph;
  if (route.name === "context") return garden?.capabilities.context;
  return true;
}

function accessDescription(garden: GardenOverview) {
  return garden.demo ? "Fictional demo" : "Scoped local session";
}

function Ecosystem() {
  return (
    <nav aria-label="Ego Hygiene projects" className="studio-ecosystem">
      {affiliated.map(([name, href]) => (
        <a href={href} rel="noreferrer" key={name}>
          {name}
          <ArrowUpRight size={12} aria-hidden="true" />
        </a>
      ))}
    </nav>
  );
}

function Sidebar({
  route,
  garden,
  navigate,
}: {
  route: Route;
  garden?: GardenOverview;
  navigate: (route: Route) => void;
}) {
  const current = route.name === "note" ? "notes" : route.name;
  return (
    <aside className="studio-sidebar">
      <button
        type="button"
        className="studio-brand"
        aria-label="Mindgarden overview"
        onClick={() => navigate({ name: "overview" })}
      >
        <img src="/garden-icon.svg" width="38" height="38" alt="" />
        <span>Mindgarden</span>
      </button>
      <nav aria-label="Garden" className="studio-nav">
        {sections.filter((item) => canOpen(item.route, garden)).map((item) => (
          <button
            type="button"
            key={item.route.name}
            className="studio-nav-item"
            aria-current={item.route.name === current ? "page" : undefined}
            onClick={() => navigate(item.route)}
          >
            <item.icon size={19} strokeWidth={1.7} aria-hidden="true" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="studio-sidebar-end">
        <div className="studio-local">
          <CircleDot size={13} aria-hidden="true" />
          <span>Local workspace</span>
        </div>
        <Ecosystem />
      </div>
    </aside>
  );
}

function SearchDialog({
  open,
  onOpen,
  onSearch,
}: {
  open: boolean;
  onOpen: (open: boolean) => void;
  onSearch: (query: string) => void;
}) {
  const field = useRef<HTMLInputElement>(null);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = new FormData(event.currentTarget).get("query");
    if (typeof value !== "string" || !value.trim()) return;
    onOpen(false);
    onSearch(value.trim());
  }
  return (
    <Dialog.Root open={open} onOpenChange={onOpen}>
      <Dialog.Trigger className="studio-search">
        <Search size={17} strokeWidth={1.8} aria-hidden="true" />
        <span>Search the garden</span>
        <kbd aria-hidden="true">⌘ K</kbd>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="studio-dialog-overlay" />
        <Dialog.Content className="studio-dialog-content" onOpenAutoFocus={(event) => {
          event.preventDefault();
          field.current?.focus();
        }}>
          <header className="studio-dialog-heading">
            <Dialog.Title>Search the garden</Dialog.Title>
            <Dialog.Close className="studio-icon-button" aria-label="Close search">
              <X size={20} aria-hidden="true" />
            </Dialog.Close>
          </header>
          <Dialog.Description className="subdued">Find reviewed notes using words or phrases.</Dialog.Description>
          <form onSubmit={submit} className="studio-search-form">
            <label htmlFor="studio-search-query" className="sr-only">Search reviewed notes</label>
            <input ref={field} id="studio-search-query" type="search" name="query" placeholder="What are you looking for?" required maxLength={QUERY_MAX_LENGTH} autoComplete="off" spellCheck={false} />
            <button className="button primary" type="submit">Search <ArrowRight size={16} aria-hidden="true" /></button>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function Metrics({ garden }: { garden: GardenOverview }) {
  const metrics = [
    { title: "Visible notes", value: garden.notes.length, icon: BookOpen, color: "leaf" },
    { title: "Source citations", value: garden.notes.reduce((sum, note) => sum + note.source_count, 0), icon: Link2, color: "sand" },
    ...(garden.capabilities.graph
      ? [{ title: "Connections", value: garden.graph.edges.length, icon: GitFork, color: "moss" }]
      : []),
  ];
  return (
    <ul className="studio-metrics" aria-label="Visible garden totals">
      {metrics.map(({ title, value, icon: Icon, color }) => (
        <li key={title} className="studio-metric">
          <span className={`studio-stat-symbol studio-tone-${color}`}><Icon size={18} strokeWidth={1.7} aria-hidden="true" /></span>
          <div>
            <strong>{value}</strong>
            <span>{title}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}

const domainStyles: Record<string, { icon: typeof BookOpen; color: string }> = {
  career: { icon: Sprout, color: "moss" },
  business: { icon: BriefcaseBusiness, color: "leaf" },
  household: { icon: House, color: "sand" },
  "financial-records": { icon: Wallet, color: "sky" },
};

function FeaturedNotes({
  notes,
  onNote,
  goToLibrary,
}: {
  notes: readonly NoteSummary[];
  onNote: (reference: string) => void;
  goToLibrary: () => void;
}) {
  return (
    <section className="panel studio-featured">
      <header className="studio-panel-header">
        <div>
          <h2>From the library</h2>
          <p>Reviewed knowledge in this session</p>
        </div>
        <button type="button" className="studio-text-button" onClick={goToLibrary}>All notes <ArrowRight size={15} aria-hidden="true" /></button>
      </header>
      {notes.length ? (
        <ul className="studio-featured-list">
          {notes.slice(0, 5).map((note) => {
            const domain = note.domains[0];
            const { color, icon: Icon } = domainStyles[domain?.replaceAll(" ", "-")] || { color: "leaf", icon: BookOpen };
            const citationLabel = note.source_count === 1 ? "citation" : "citations";
            return (
              <li key={referenceKey(note.reference)}>
                <button type="button" className="studio-note-preview" onClick={() => onNote(referenceKey(note.reference))}>
                  <span className={`studio-stat-symbol studio-tone-${color}`}><Icon size={18} strokeWidth={1.7} aria-hidden="true" /></span>
                  <span className="studio-preview-text">
                    <strong>{note.title}</strong>
                    <small>{domain?.replaceAll("-", " ") || note.kind}{` · ${note.source_count} ${citationLabel}`}</small>
                  </span>
                  <ArrowUpRight className="studio-preview-arrow" size={16} aria-hidden="true" />
                </button>
              </li>
            );
          })}
        </ul>
      ) : <p className="subdued">There are no visible reviewed notes in this session.</p>}
    </section>
  );
}

function Overview({ garden, navigate, onNote }: {
  garden: GardenOverview;
  navigate: (route: Route) => void;
  onNote: (reference: string) => void;
}) {
  return (
    <>
      <section className="studio-hero">
        <div className="studio-hero-content">
          <p className="studio-workspace-label"><Sprout size={16} aria-hidden="true" /> {accessDescription(garden)}</p>
          <h1>See how your<br className="hero-break" /> knowledge connects.</h1>
          <p className="studio-hero-summary">A quiet place to explore reviewed notes, follow their connections, and find the sources behind them.</p>
          <div className="studio-hero-actions">
            <button className="button primary" type="button" onClick={() => navigate({ name: "notes", query: "" })}>
              Explore the library <ArrowRight size={17} aria-hidden="true" />
            </button>
            {garden.capabilities.context && (
              <button className="button studio-hero-secondary" type="button" onClick={() => navigate({ name: "context", query: "" })}>
                Build a context pack <Layers3 size={16} aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
      </section>
      <Metrics garden={garden} />
      <div className={`studio-overview-grid${garden.capabilities.graph ? "" : " studio-single-column"}`}>
        <FeaturedNotes notes={garden.notes} onNote={onNote} goToLibrary={() => navigate({ name: "notes", query: "" })} />
        {garden.capabilities.graph && (
          <section className="panel studio-graph-preview">
            <header className="studio-panel-header">
              <div><h2>Garden map</h2><p>Relationships between visible notes</p></div>
              <button type="button" className="studio-text-button" onClick={() => navigate({ name: "connections" })}>Open map <ArrowRight size={15} aria-hidden="true" /></button>
            </header>
            <GardenGraph garden={garden} onNote={onNote} compact />
          </section>
        )}
      </div>
      {garden.limited && <p className="subdued studio-budget-note">The active session limits how many records this view can show.</p>}
    </>
  );
}

function Connections({ garden, onNote }: { garden: GardenOverview; onNote: (reference: string) => void }) {
  return (
    <>
      <header className="studio-page-heading">
        <h1>Connections</h1>
        <p>Follow the links between notes. Switch to 3D to rotate the same graph.</p>
      </header>
      <section className="panel studio-graph-page" aria-label="Garden map">
        <GardenGraph garden={garden} onNote={onNote} />
      </section>
    </>
  );
}

function currentSection(route: Route) {
  const name = route.name === "note" ? "notes" : route.name;
  return sections.find((item) => item.route.name === name)?.label || "Overview";
}

export function Studio({ client }: { client: GardenClient }) {
  const [route, setRoute] = useState<Route>({ name: "overview" });
  const [garden, setGarden] = useState<GardenOverview>();
  const [error, setError] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const main = useRef<HTMLElement>(null);
  const afterNavigation = useRef(false);
  const libraryReturn = useRef<Route>({ name: "notes", query: "" });
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const controller = new AbortController();
    client.garden(controller.signal).then((next) => {
      if (!controller.signal.aborted) setGarden(next);
    }).catch((problem: unknown) => {
      if (!controller.signal.aborted) setError(problem instanceof Error ? problem.message : "Couldn't open the garden.");
    });
    return () => controller.abort();
  }, [client, route]);

  useEffect(() => {
    if ((garden || error) && afterNavigation.current) {
      afterNavigation.current = false;
      window.scrollTo(0, 0);
      main.current?.focus({ preventScroll: true });
    }
  }, [garden, error]);

  useEffect(() => {
    if (!garden?.capabilities.search) return;
    function shortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, [garden?.capabilities.search]);

  function navigate(next: Route) {
    afterNavigation.current = true;
    setSearchOpen(false);
    setGarden(undefined);
    setError("");
    setRoute({ ...next });
  }

  function openNote(reference: string) {
    if (route.name === "notes") libraryReturn.current = route;
    else if (route.name !== "note") libraryReturn.current = { name: "notes", query: "" };
    navigate({ name: "note", reference });
  }
  const search = (query: string) => navigate({ name: "notes", query });
  let content: ReactNode;
  if (error) {
    content = <section className="panel studio-notice"><h1>Open your garden</h1><p role="alert">{error}</p><button className="button" type="button" onClick={() => navigate({ ...route })}>Try again</button></section>;
  } else if (!garden) {
    content = <p className="studio-loading" role="status"><span className="studio-loading-dot" /> Opening your garden…</p>;
  } else if (!canOpen(route, garden)) {
    content = <section className="panel studio-notice"><h1>{currentSection(route)}</h1><p>This view is unavailable in the active session.</p></section>;
  } else {
    switch (route.name) {
      case "overview": content = <Overview garden={garden} navigate={navigate} onNote={openNote} />; break;
      case "connections": content = <Connections garden={garden} onNote={openNote} />; break;
      case "notes": content = <NotesView client={client} notes={garden.notes} query={route.query} onSearch={search} onOpenNote={openNote} canSearch={garden.capabilities.search} />; break;
      case "note": content = <NoteView client={client} reference={route.reference} onOpenNote={openNote} onBack={() => navigate(libraryReturn.current)} canReadEvidence={garden.capabilities.evidence} notes={garden.notes} />; break;
      case "context": content = <ContextView client={client} query={route.query} notes={garden.notes} onBuild={(query) => navigate({ name: "context", query })} onOpenNote={openNote} enabled={garden.capabilities.context} />; break;
    }
  }

  return (
    <div className="studio-app">
      <a className="studio-skip" href="#main">Skip to content</a>
      <Sidebar route={route} garden={garden} navigate={navigate} />
      <div className="studio-workspace min-w-0">
        <header className="studio-topbar">
          <div className="studio-location">
            <span className="studio-workspace-icon"><Sprout size={19} strokeWidth={1.8} aria-hidden="true" /></span>
            <div className="min-w-0"><strong>{garden?.title || "Mindgarden"}</strong><span>{currentSection(route)}</span></div>
          </div>
          {garden?.capabilities.search && <SearchDialog open={searchOpen} onOpen={setSearchOpen} onSearch={search} />}
        </header>
        <main id="main" ref={main} tabIndex={-1} aria-busy={!garden && !error}>
          {garden ? (
            <motion.div key={route.name} initial={reducedMotion ? false : { opacity: 0.75, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.26 }}>
              {content}
            </motion.div>
          ) : content}
        </main>
        <footer className="studio-footer">
          <span>Mindgarden Studio</span>
          <span>{garden ? accessDescription(garden) : "Local workspace"}</span>
          <Ecosystem />
        </footer>
      </div>
    </div>
  );
}
