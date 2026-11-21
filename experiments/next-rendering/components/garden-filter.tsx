"use client";

import { useId, useState } from "react";

type Entry = {
  id: string;
  title: string;
  domains: string[];
  topics: string[];
  body: string;
  uncertainty: string[];
};

export function GardenFilter({ entries }: { entries: Entry[] }) {
  const filterId = useId();
  const [domain, setDomain] = useState("");
  const domains = [...new Set(entries.flatMap((entry) => entry.domains))].sort();
  const visible = domain ? entries.filter((entry) => entry.domains.includes(domain)) : entries;

  return (
    <section aria-labelledby="garden-notes" className="garden-notes">
      <div className="notes-header">
        <div>
          <h2 id="garden-notes">Fictional garden notes</h2>
          <p>Filter these notes in the browser. The render ID stays the same.</p>
        </div>
        <div className="filter">
          <label htmlFor={filterId}>Domain</label>
          <select id={filterId} value={domain} onChange={(event) => setDomain(event.target.value)}>
            <option value="">All domains</option>
            {domains.map((name) => (
              <option key={name} value={name}>{name[0].toUpperCase() + name.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>
      <p className="result-count" aria-live="polite">
        {visible.length} of {entries.length} notes
      </p>
      <ul className="note-grid">
        {visible.map((entry) => (
          <li key={entry.id} className="note-card">
            <p className="domain">{entry.domains.join(" · ")}</p>
            <h3>{entry.title}</h3>
            <p>{entry.body}</p>
            {entry.uncertainty.map((item) => (
              <p className="uncertainty" key={item}>{item}</p>
            ))}
            <ul className="topics" aria-label="Topics">
              {entry.topics.map((topic) => <li key={topic}>{topic}</li>)}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  );
}
