import { ArrowRight, ArrowUpRight, CloudDownload, HardDrive, Terminal } from "lucide-react";
import type { ConnectorSummary } from "./api";
import "./connectors.css";

const driveGuide = "https://github.com/egohygiene/mindgarden/blob/main/docs/drive-capture.md";

const driveStates = {
  demo: {
    label: "Fictional example",
    tone: "quiet",
    detail: "The demo uses made-up sources. You can explore it before configuring a Google Drive capture.",
  },
  captured: {
    label: "Captured evidence",
    tone: "available",
    detail: "Reviewed notes in this session cite an earlier Drive capture. Their citations point to the preserved snapshot.",
  },
  "setup-required": {
    label: "No visible Drive capture",
    tone: "setup",
    detail: "This session has no reviewed Drive citations. See the capture guide to add and review a selected snapshot.",
  },
};

const vaultStates = {
  "visible-evidence": {
    label: "Evidence available",
    tone: "available",
    detail: "Reviewed notes in this session cite evidence preserved in the local source vault.",
  },
  "no-visible-evidence": {
    label: "No visible evidence",
    tone: "quiet",
    detail: "This session has no reviewed citations backed by the local source vault.",
  },
};

const steps = [
  {
    title: "Authorize read-only access",
    command: "mindgarden capture authorize --help",
    detail: "Set up the optional Google OAuth helper on your machine. Keep the credential files outside the garden and Git.",
  },
  {
    title: "Review and capture selected files",
    command: "mindgarden capture drive --help",
    detail: "Preview the folders or files, scope, destination, and limits. Apply the reviewed digest with explicit network permission.",
  },
  {
    title: "Import and review the evidence",
    command: "mindgarden ingest --help",
    detail: "Normalize the frozen capture and review the resulting knowledge. Its citations can then appear in Studio.",
  },
];

function describeConnectors(summary: ConnectorSummary) {
  return [
    {
      name: "Google Drive",
      icon: CloudDownload,
      color: "sky",
      count: summary.google_drive.citation_count,
      ...driveStates[summary.google_drive.state],
    },
    {
      name: "Local source vault",
      icon: HardDrive,
      color: "moss",
      count: summary.local_vault.citation_count,
      ...vaultStates[summary.local_vault.state],
    },
  ];
}

function citationLabel(count: number) {
  return count === 1 ? "reviewed citation" : "reviewed citations";
}

function SetupGuide() {
  return (
    <section className="panel connector-guide" aria-labelledby="connector-guide-title">
      <header className="studio-panel-header">
        <div>
          <h2 id="connector-guide-title">Capture from Google Drive</h2>
          <p>Use the terminal to capture a private snapshot. Studio shows the evidence after review.</p>
        </div>
      </header>
      <ol className="connector-steps">
        {steps.map(({ title, command, detail }) => (
          <li key={command}>
            <h3>{title}</h3>
            <p>{detail}</p>
            <span className="connector-command"><Terminal size={14} aria-hidden="true" /> <code>{command}</code></span>
          </li>
        ))}
      </ol>
      <a className="button connector-guide-link" href={driveGuide} rel="noreferrer">
        Read the Drive capture guide <ArrowUpRight size={15} aria-hidden="true" />
      </a>
    </section>
  );
}

export function SourcesView({ connectors, error }: {
  connectors: ConnectorSummary | undefined;
  error?: string;
}) {
  return (
    <div className="connector-page">
      <header className="studio-page-heading">
        <h1>Sources</h1>
        <p>See where reviewed evidence in this session came from. Drive evidence reflects captured snapshots.</p>
      </header>
      {error ? <p className="panel connector-feedback connector-error" role="alert">Source availability could not be verified for this session.</p>
        : connectors ? <div className="connector-grid">
          {describeConnectors(connectors).map(({ name, icon: Icon, color, count, label, detail, tone }) => (
            <article className="panel connector-card" key={name}>
              <header className="connector-card-top">
                <span className={`connector-icon studio-tone-${color}`}><Icon size={25} strokeWidth={1.65} aria-hidden="true" /></span>
                <span className={`connector-tag connector-tag-${tone}`}>{label}</span>
              </header>
              <h2>{name}</h2>
              <p className="connector-detail">{detail}</p>
              <p className="connector-count"><strong>{count.toLocaleString()}</strong> {citationLabel(count)}</p>
            </article>
          ))}
        </div> : <p className="panel connector-feedback" role="status">Checking evidence in this session…</p>}
      <SetupGuide />
    </div>
  );
}

export function ConnectorPreview({ connectors, error, onOpen }: {
  connectors?: ConnectorSummary;
  error?: string;
  onOpen: () => void;
}) {
  return (
    <section className="panel connector-preview">
      <header className="studio-panel-header">
        <h2>Sources</h2>
        <button type="button" className="studio-text-button" onClick={onOpen}>
          View sources <ArrowRight size={15} aria-hidden="true" />
        </button>
      </header>
      {error ? <p className="subdued">Source details are unavailable in this session.</p>
        : connectors ? <ul className="connector-preview-list">
        {describeConnectors(connectors).map(({ name, icon: Icon, color, count, label }) => (
          <li key={name}>
            <span className={`connector-preview-icon studio-tone-${color}`}><Icon size={18} strokeWidth={1.7} aria-hidden="true" /></span>
            <span className="connector-preview-description">
              <strong>{name}</strong><span>{label} · {count.toLocaleString()} {citationLabel(count)}</span>
            </span>
          </li>
        ))}
      </ul> : <p className="subdued">Open Sources for evidence availability and Drive setup.</p>}
    </section>
  );
}
