"use strict";

const main = document.querySelector("#main");
const announcements = document.querySelector("#announcements");
const globalQuery = document.querySelector("#global-query");
const headings = { overview: "Overview", notes: "Notes", connections: "Connections", context: "Context pack", note: "Note" };
const svgNS = "http://www.w3.org/2000/svg";
const icons = {
  home: "M3 10l9-7 9 7v10H3z M9 20v-6h6v6",
  notes: "M5 3h11l3 3v15H5z M15 3v5h4 M8 12h8 M8 16h6",
  branch: "M7 8v8 M9 7l7 4 M9 17l7-4 M9 6a2 2 0 1 1-4 0 2 2 0 1 1 4 0 M9 18a2 2 0 1 1-4 0 2 2 0 1 1 4 0 M20 12a2 2 0 1 1-4 0 2 2 0 1 1 4 0",
  layers: "M12 3l9 5-9 5-9-5z M3 12l9 5 9-5 M3 16l9 5 9-5",
  search: "M16 16l4 4 M18 11a7 7 0 1 1-14 0 7 7 0 1 1 14 0",
  link: "M10 13l4-4 M8 15l-1 1a3 3 0 1 1-4-4l4-4a3 3 0 0 1 4 0 M16 9l1-1a3 3 0 1 1 4 4l-4 4a3 3 0 0 1-4 0",
  arrow: "M4 12h15 M13 6l6 6-6 6",
};

const initialFragment = new URLSearchParams(location.hash.slice(1));
let access = initialFragment.get("access");
try {
  if (access) sessionStorage.setItem("mindgarden-access", access);
  else access = sessionStorage.getItem("mindgarden-access");
} catch {
  // The visit can still run when the browser disables session storage.
}
if (initialFragment.has("access")) history.replaceState(null, "", "#overview");

let garden;
let savedNotes = new Map();
let renderVersion = 0;

function element(tag, classes, value) {
  const node = document.createElement(tag);
  if (classes) node.className = classes;
  if (value !== undefined) node.textContent = value;
  return node;
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(svgNS, tag);
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  return node;
}

function icon(name) {
  const svg = svgElement("svg", { class: "icon", viewBox: "0 0 24 24", "aria-hidden": "true" });
  svg.append(svgElement("path", {
    d: icons[name], fill: "none", stroke: "currentColor", "stroke-width": 1.65,
    "stroke-linecap": "round", "stroke-linejoin": "round",
  }));
  return svg;
}

for (const placeholder of document.querySelectorAll("[data-icon]")) {
  placeholder.replaceWith(icon(placeholder.dataset.icon));
}

function referenceKey(reference) {
  return reference && typeof reference === "object" ? reference.garden + "/" + reference.id : reference || "";
}

function route(view, params = {}) {
  const query = new URLSearchParams(params).toString();
  return "#" + view + (query ? "?" + query : "");
}

function anchor(value, href, classes) {
  const link = element("a", classes, value);
  link.href = href;
  return link;
}

function noteLink(note, classes) {
  return anchor(note.title, route("note", { ref: referenceKey(note.reference) }), classes);
}

function message(value, problem = false) {
  const node = element("p", problem ? "message error" : "message", value);
  if (problem) node.setAttribute("role", "alert");
  return node;
}

async function request(name, params = {}, retainText = false) {
  if (!access) throw new Error("Open the complete visit link printed in your terminal.");
  const query = new URLSearchParams(params).toString();
  const response = await fetch("/api/" + name + (query ? "?" + query : ""), {
    headers: { Authorization: "Bearer " + access },
    cache: "no-store",
  });
  const text = await response.text();
  const payload = JSON.parse(text);
  if (!response.ok) throw new Error(payload.error?.message || "This view is unavailable.");
  return retainText ? { payload, text } : payload;
}

function heading(title, detail) {
  const header = element("header", "page-heading");
  header.append(element("h1", "", title));
  if (detail) header.append(element("p", "", detail));
  return header;
}

function panel(title, action) {
  const section = element("section", "panel");
  const header = element("header", "panel-header");
  header.append(element("h2", "", title));
  if (action) header.append(action);
  section.append(header);
  return section;
}

function pretty(value) {
  return typeof value === "string" ? value.replaceAll("-", " ").replaceAll("_", " ") : "";
}

function noteMetadata(note) {
  const fields = [...(note.domains || []).map(pretty), pretty(note.review?.state), pretty(note.scope?.visibility)];
  return fields.filter(Boolean).join(" · ");
}

function quantity(number, subject) {
  return number + " " + subject + (number === 1 ? "" : "s");
}

function noteRows(notes) {
  if (!notes.length) return message("There are no matching notes in this session.");
  const list = element("ul", "list");
  for (const note of notes) {
    const row = element("li", "note-row");
    const marker = element("div", "note-marker");
    marker.append(icon("notes"));
    const item = element("div");
    item.append(noteLink(note), element("p", "note-meta", noteMetadata(note)));
    if (note.snippet) item.append(element("p", "result-snippet", note.snippet));
    if (note.selection_reasons?.length) {
      const fields = [...new Set(note.selection_reasons.map((reason) => pretty(reason.field)).filter(Boolean))];
      if (fields.length) item.append(element("p", "detail", "Matches in " + fields.join(", ")));
    }
    row.append(marker, item);
    list.append(row);
  }
  return list;
}

function graphLabel(note) {
  const words = note.title.replace(/^(Fictional|Synthetic)\s+/i, "").split(/\s+/)
    .filter((word) => !["and", "of", "the"].includes(word.toLowerCase()));
  const pair = words.slice(0, 2).join(" ");
  const label = pair.length <= 22 ? pair : words[0];
  return (label || note.title).slice(0, 22).replace(/^./, (letter) => letter.toUpperCase());
}

function graphFigure(graph, preview = false) {
  const limit = preview ? 8 : 14;
  const allNodes = graph.nodes || [];
  const nodes = allNodes.slice(0, limit);
  const figure = element("figure", "graph-figure");
  if (!nodes.length) {
    figure.append(element("p", "graph-empty", "There are no connected notes in this view."));
    return figure;
  }
  const coordinates = new Map();
  const svg = svgElement("svg", { viewBox: "0 0 510 278", role: "group", "aria-label": "Connections between visible notes" });
  nodes.forEach((note, index) => {
    const angle = (2 * Math.PI * (index - 1) / nodes.length);
    const x = nodes.length === 1 ? 255 : 255 + 165 * Math.cos(angle);
    const y = nodes.length === 1 ? 125 : 122 + 78 * Math.sin(angle);
    coordinates.set(referenceKey(note.reference), { x, y });
  });
  for (const edge of graph.edges || []) {
    const source = coordinates.get(edge.source);
    const target = coordinates.get(edge.target);
    if (!source || !target) continue;
    svg.append(svgElement("line", {
      class: "graph-edge", x1: source.x, y1: source.y, x2: target.x, y2: target.y, "aria-hidden": "true",
    }));
  }
  for (const note of nodes) {
    const key = referenceKey(note.reference);
    const { x, y } = coordinates.get(key);
    const node = svgElement("a", { class: "graph-node", href: route("note", { ref: key }), "aria-label": note.title });
    node.append(svgElement("circle", { cx: x, cy: y, r: 23 }));
    node.append(svgElement("circle", { cx: x, cy: y, r: 12 }));
    const label = svgElement("text", { x, y: y + 31, "aria-hidden": "true" });
    label.textContent = graphLabel(note);
    node.append(label);
    svg.append(node);
  }
  figure.append(svg);
  if (allNodes.length > limit) {
    figure.append(element("figcaption", "graph-empty", "The diagram shows " + limit + " of " + allNodes.length + " visible notes."));
  }
  return figure;
}

function metrics(notes, edges) {
  const list = element("ul", "metrics list");
  list.setAttribute("aria-label", "Visible garden totals");
  const sourceCount = notes.reduce((total, note) => total + (note.source_count || 0), 0);
  for (const [label, count, symbol] of [
    ["Visible notes", notes.length, "notes"], ["Source citations", sourceCount, "link"], ["Connections", edges.length, "branch"],
  ]) {
    const card = element("li", "metric");
    const marker = element("div", "metric-symbol");
    marker.append(icon(symbol));
    card.append(marker, element("span", "metric-value", count), element("span", "metric-description", label));
    list.append(card);
  }
  return list;
}

function overview() {
  const notes = garden.notes || [];
  const graph = garden.graph || { nodes: [], edges: [] };
  const hero = element("section", "hero");
  const inner = element("div", "hero-content");
  const label = element("span", "hero-label", garden.demo ? "Fictional demo garden" : "Scoped local garden");
  const cta = anchor("Explore notes", "#notes", "button primary");
  cta.append(icon("arrow"));
  inner.append(label, element("h1", "", "A garden for what you know."), element("p", "",
    "Explore reviewed notes, follow their connections, and see the evidence behind them."), cta);
  hero.append(inner);
  const columns = element("div", "overview-grid");
  const recent = panel("Explore the garden", anchor("All notes", "#notes", "text-link"));
  recent.append(noteRows(notes.slice(0, 5)));
  columns.append(recent);
  if (garden.capabilities.graph) {
    const connections = panel("How ideas connect", anchor("View connections", "#connections", "text-link"));
    connections.append(graphFigure(graph, true), element("p", "note-meta", "Select a point to open its note."));
    columns.append(connections);
  }
  const result = [hero, metrics(notes, graph.edges), columns];
  if (garden.limited) result.push(element("p", "detail", "This view is limited by the active session budget."));
  return result;
}

function queryForm(view, label, query, submitLabel) {
  const form = element("form", "query-form");
  const field = element("div", "query-field");
  const caption = element("label", "", label);
  const input = element("input");
  input.type = "search";
  input.id = "view-query";
  input.value = query;
  input.maxLength = 200;
  input.required = view === "context";
  caption.htmlFor = input.id;
  field.append(caption, input);
  const submit = element("button", "button primary", submitLabel);
  submit.type = "submit";
  form.append(field, submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    location.hash = route(view, input.value.trim() ? { q: input.value.trim() } : {});
  });
  return form;
}

async function notesView(query) {
  const title = heading("Notes", "Browse what this session can see, or search by words and phrases.");
  const result = [title];
  if (garden.capabilities.search) result.push(queryForm("notes", "Search notes", query, "Search"));
  const data = query ? (await request("search", { q: query })).results : garden.notes;
  const listing = panel(query ? "Search results" : "All visible notes");
  listing.append(noteRows(data));
  result.push(listing);
  return result;
}

function connectionsView() {
  const description = heading("Connections", "See which notes are related and follow the links between them.");
  if (!garden.capabilities.graph) return [description, message("This session does not allow the connections view.")];
  const graph = garden.graph;
  const diagram = panel("Garden map");
  diagram.append(graphFigure(graph));
  const list = panel("Linked notes");
  const edges = element("ul", "relationships");
  for (const relation of graph.edges || []) {
    const source = savedNotes.get(relation.source);
    const target = savedNotes.get(relation.target);
    if (!source || !target) continue;
    const entry = element("li");
    entry.append(noteLink(source), document.createTextNode(" → " + pretty(relation.type) + " → "), noteLink(target));
    edges.append(entry);
  }
  list.append(edges.children.length ? edges : element("p", "detail", "No relationships are visible in this session."));
  return [description, diagram, element("div", "section-separated"), list];
}

function citationItem(citation, noteRef, index) {
  const entry = element("li", "citation");
  entry.append(element("p", "", referenceKey(citation.source)));
  entry.append(element("code", "", [citation.source?.revision, citation.locator].filter(Boolean).join(" · ")));
  entry.append(element("code", "detail", citation.content_sha256));
  if (noteRef && garden.capabilities.evidence) {
    const button = element("button", "button", "Open source excerpt");
    button.type = "button";
    const excerpt = element("div");
    excerpt.hidden = true;
    excerpt.id = "citation-" + index;
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", excerpt.id);
    button.addEventListener("click", async () => {
      if (button.hasAttribute("aria-disabled")) return;
      if (!excerpt.hidden) {
        excerpt.hidden = true;
        button.setAttribute("aria-expanded", "false");
        button.textContent = "Open source excerpt";
        return;
      }
      button.setAttribute("aria-disabled", "true");
      try {
        const found = await request("evidence", { ref: noteRef, citation: index });
        excerpt.replaceChildren(element("p", "evidence-text", found.text || "No text excerpt is available."));
      } catch (error) {
        excerpt.replaceChildren(message(error.message, true));
      } finally {
        button.textContent = "Hide source excerpt";
        button.removeAttribute("aria-disabled");
        button.setAttribute("aria-expanded", "true");
        excerpt.hidden = false;
      }
    });
    entry.append(button, excerpt);
  }
  return entry;
}

function citationList(sources, noteRef) {
  const list = element("ul", "list");
  (sources || []).forEach((source, index) => list.append(citationItem(source, noteRef, index)));
  return list.children.length ? list : element("p", "detail", "No source citations are visible.");
}

function showRelations(title, relations) {
  if (!relations?.length) return null;
  const list = element("ul", "relationships");
  for (const related of relations) {
    const key = referenceKey(related.reference || related.to || related.from);
    const item = element("li");
    item.append(noteLink({ title: related.title || savedNotes.get(key)?.title || key, reference: key }),
      document.createTextNode(" · " + pretty(related.type)));
    list.append(item);
  }
  const area = panel(title);
  area.append(list);
  return area;
}

function qualificationsPanel(qualifications) {
  const { uncertainty = [], caveats = [], contradictions = [] } = qualifications || {};
  if (!uncertainty.length && !caveats.length && !contradictions.length) return null;
  const section = panel("Questions and caveats");
  const list = element("ul", "relationships");
  for (const text of [...uncertainty, ...caveats]) list.append(element("li", "", text));
  for (const reference of contradictions) {
    const key = referenceKey(reference);
    const item = element("li", "", "Conflicting account in ");
    item.append(noteLink({ title: savedNotes.get(key)?.title || key, reference: key }));
    list.append(item);
  }
  section.append(list);
  return section;
}

async function noteView(key) {
  const { note, links, backlinks } = await request("note", { ref: key });
  const pageHeading = heading(note.title, noteMetadata(note));
  pageHeading.prepend(anchor("← All notes", "#notes", "text-link"));
  const reading = panel("Reviewed knowledge");
  reading.classList.add("reading");
  reading.append(element("p", "note-text", note.content));
  const evidence = panel("Source citations");
  evidence.append(citationList(note.sources, key));
  const grid = element("div", "reading-grid");
  grid.append(reading, evidence);
  for (const section of [
    qualificationsPanel(note.qualifications),
    showRelations("Related notes", links),
    showRelations("Linked from", backlinks),
  ]) {
    if (section) grid.append(section);
  }
  return [pageHeading, grid];
}

function downloadPack(text) {
  const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
  const link = anchor("Download", url);
  link.download = "mindgarden-context.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function contextView(query) {
  const title = heading("Context pack", "Gather a small, cited set of notes for a question or task.");
  if (!garden.capabilities.context) return [title, message("This session does not allow context packs.")];
  const form = queryForm("context", "Topic or keywords", query, "Build context pack");
  if (!query) return [title, form];
  const { payload: pack, text } = await request("context", { q: query }, true);
  const result = panel("Included notes");
  const summary = [
    quantity(pack.included.length, "note"),
    pack.budget.max_bytes.toLocaleString() + "-byte limit",
    pretty(pack.scope?.visibility),
  ].filter(Boolean).join(" · ");
  result.append(element("p", "detail", summary));
  if (pack.included.length) {
    const download = element("button", "button", "Download JSON");
    download.addEventListener("click", () => downloadPack(text));
    const actions = element("div", "query-actions");
    actions.append(download);
    result.append(actions);
  }
  for (const note of pack.included) {
    const key = referenceKey(note.reference);
    const article = element("article", "context-item");
    const title = element("h3");
    title.append(noteLink({ reference: key, title: savedNotes.get(key)?.title || key }));
    article.append(title, element("p", "note-text", note.content),
      element("p", "detail", note.selection_reason === "lexical-query" ? "Selected by keyword match" : "Explicitly selected"),
      citationList(note.sources));
    result.append(article);
  }
  if (!pack.included.length) result.append(message("No matching notes fit this pack. Try another topic."));
  return [title, form, result];
}

async function render(focus = false) {
  if (!garden) return;
  const [fragment, query] = location.hash.slice(1).split("?", 2);
  if (fragment === "main") return;
  const view = Object.hasOwn(headings, fragment) ? fragment : "overview";
  const version = ++renderVersion;
  const parameters = new URLSearchParams(query);
  const keyword = parameters.get("q") || "";
  main.setAttribute("aria-busy", "true");
  document.querySelector("#view-title").textContent = headings[view];
  for (const link of document.querySelectorAll("[data-view]")) {
    if (link.dataset.view === (view === "note" ? "notes" : view)) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  let contents;
  try {
    if (focus) updateGarden(await request("garden"));
    if (version !== renderVersion) return;
    switch (view) {
      case "notes": contents = await notesView(keyword); break;
      case "connections": contents = connectionsView(); break;
      case "context": contents = await contextView(keyword); break;
      case "note": contents = await noteView(parameters.get("ref") || ""); break;
      default: contents = overview();
    }
  } catch (error) {
    contents = [heading(headings[view]), message(error.message, true)];
  }
  if (version !== renderVersion) return;
  const section = element("div", "enter");
  section.append(...contents);
  main.replaceChildren(section);
  main.setAttribute("aria-busy", "false");
  document.title = headings[view] + " · Mindgarden";
  announcements.textContent = headings[view] + " ready";
  if (focus) {
    window.scrollTo(0, 0);
    main.focus({ preventScroll: true });
  }
}

document.querySelector("#quick-search").addEventListener("submit", (event) => {
  event.preventDefault();
  if (globalQuery.value.trim()) location.hash = route("notes", { q: globalQuery.value.trim() });
});
window.addEventListener("hashchange", () => render(true));

async function openGarden() {
  main.setAttribute("aria-busy", "true");
  main.replaceChildren(element("p", "loading", "Opening your garden…"));
  try {
    updateGarden(await request("garden"));
    await render();
  } catch (error) {
    main.replaceChildren(heading("Open your garden"), message(error.message, true));
    main.setAttribute("aria-busy", "false");
  }
}

function updateGarden(view) {
  garden = view;
  savedNotes = new Map((view.notes || []).map((note) => [referenceKey(note.reference), note]));
  document.querySelector("#garden-title").textContent = view.title;
  document.querySelector("#footer-scope").textContent = view.demo ? "Fictional data · Runs locally" : "Scoped session · Runs locally";
  document.querySelector("#quick-search").hidden = !view.capabilities.search;
  document.querySelector('[data-view="connections"]').hidden = !view.capabilities.graph;
  document.querySelector('[data-view="context"]').hidden = !view.capabilities.context;
}

openGarden();
