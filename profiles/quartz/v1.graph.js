/* Copyright 2026 Ego Hygiene. SPDX-License-Identifier: MIT. */
(() => {
  if (window.mindgardenGraphInstalled) return;
  window.mindgardenGraphInstalled = true;
  const base = new URL("../../", document.currentScript.src);
  const namespace = "http://www.w3.org/2000/svg";
  function element(name, attributes, text) {
    const node = document.createElementNS(namespace, name);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
    if (text !== undefined) node.textContent = text;
    return node;
  }
  async function render() {
    const host = document.getElementById("mindgarden-graph");
    if (!host || host.dataset.rendered) return;
    host.dataset.rendered = "true";
    const status = host.querySelector("[role=status]");
    try {
      const [graph, index] = await Promise.all(["graph.json", "index.json"].map(async name => {
        const response = await fetch(new URL(name, base), {credentials: "omit"});
        if (!response.ok) throw new Error("Unavailable graph");
        return response.json();
      }));
      if (graph.schema !== "mindgarden.federation-graph/v1" || index.schema !== "mindgarden.federation-index/v1") throw new Error("Unsupported graph");
      if (graph.nodes.length > 200) {
        status.textContent = "This selection exceeds the 200-node interactive preview budget. The complete relationship list remains below.";
        return;
      }
      const records = new Map(index.records.map(record => [record.reference.id, record]));
      const nodes = graph.nodes.filter(node => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(node.id) && records.has(node.id));
      const svg = host.querySelector("svg");
      svg.replaceChildren();
      const positions = new Map(nodes.map((node, i) => [node.id, {x: 400 + 265 * Math.cos(2 * Math.PI * i / Math.max(nodes.length, 1)), y: 260 + 170 * Math.sin(2 * Math.PI * i / Math.max(nodes.length, 1))}]));
      for (const edge of graph.edges) {
        const from = positions.get(edge.source.id), to = positions.get(edge.target.id);
        if (from && to) {
          const line = element("line", {x1: from.x, y1: from.y, x2: to.x, y2: to.y, class: "mindgarden-edge"});
          line.append(element("title", {}, edge.type));
          svg.append(line);
        }
      }
      for (const node of nodes) {
        const position = positions.get(node.id), record = records.get(node.id);
        const link = element("a", {href: new URL("notes/" + encodeURIComponent(node.id) + "/", base).href, "aria-label": record.title, tabindex: 0});
        link.append(element("circle", {cx: position.x, cy: position.y, r: 13, class: "mindgarden-node"}));
        link.append(element("text", {x: position.x, y: position.y + 32, "text-anchor": "middle", class: "mindgarden-node-label"}, node.id));
        svg.append(link);
      }
      let zoom = 1;
      function update(delta) {
        zoom = Math.max(0.5, Math.min(3, zoom + delta));
        svg.setAttribute("viewBox", `${400 - 400 / zoom} ${260 - 260 / zoom} ${800 / zoom} ${520 / zoom}`);
      }
      host.querySelector('[data-zoom="in"]').onclick = () => update(0.25);
      host.querySelector('[data-zoom="out"]').onclick = () => update(-0.25);
      host.querySelector('[data-zoom="reset"]').onclick = () => { zoom = 1; update(0); };
      status.textContent = nodes.length ? "Use Tab to select a note, or the zoom controls to explore. The complete typed relationships are listed below." : "No reviewed nodes are selected yet.";
    } catch (_) {
      status.textContent = "The interactive view is unavailable. The complete relationship list remains below.";
    }
  }
  document.addEventListener("DOMContentLoaded", render);
  document.addEventListener("nav", render);
  document.addEventListener("render", render);
  render();
})();
