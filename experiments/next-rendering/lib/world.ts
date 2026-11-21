import "server-only";

import world from "../../../examples/mock-garden/world.json";

export function readFictionalGarden() {
  if (world.schema !== "mindgarden.mock-garden-seed/v1" || world.fictional !== true) {
    throw new Error("The rendering experiment requires the fictional garden fixture.");
  }

  return world.entries.map(({ id, title, domains, topics, body, uncertainty }) => ({
    id,
    title: title.replace(/^Fictional /, ""),
    domains,
    topics,
    body: body.replace(/^Entirely fictional: /, "").trim(),
    uncertainty,
  }));
}
