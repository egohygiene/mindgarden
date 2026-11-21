import { randomUUID } from "node:crypto";
import { readFictionalGarden } from "../lib/world";
import { GardenFilter } from "./garden-filter";

type RenderingMode = "static" | "request-time";

const modes = {
  static: {
    path: "/",
    title: "Built once",
    label: "Build-time rendering",
    description: "Next.js rendered this page during the production build. Request it again to see the same time and render ID.",
  },
  "request-time": {
    path: "/request-time",
    title: "Built on request",
    label: "Request-time rendering",
    description: "Next.js renders this page when your request arrives. Request it again to see a fresh time and render ID.",
  },
} as const;

export function RenderingPage({ mode }: { mode: RenderingMode }) {
  const sample = modes[mode];
  const time = new Date().toISOString();
  const renderId = randomUUID();

  return (
    <>
      <header className="site-header">
        <span className="wordmark">Mindgarden <span>/</span> Rendering lab</span>
        <nav aria-label="Rendering mode">
          <a href="/" aria-current={mode === "static" ? "page" : undefined}>Build time</a>
          <a href="/request-time" aria-current={mode === "request-time" ? "page" : undefined}>Request time</a>
        </nav>
      </header>
      <main>
        <section className="hero" aria-labelledby="rendering-title">
          <div className="hero-copy">
            <p className="rendering-label">{sample.label}</p>
            <h1 id="rendering-title">{sample.title}</h1>
            <p>{sample.description}</p>
          </div>
          <div className="render-details">
            <dl>
              <dt>Rendered at (UTC)</dt>
              <dd><time dateTime={time} data-render-time="">{time}</time></dd>
              <dt>Render ID</dt>
              <dd><code data-render-id="">{renderId}</code></dd>
            </dl>
            <form action={sample.path} method="get">
              <button type="submit">Request again</button>
            </form>
          </div>
        </section>
        <GardenFilter entries={readFictionalGarden()} />
      </main>
    </>
  );
}
