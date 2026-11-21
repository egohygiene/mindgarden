import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const config: NextConfig = {
  poweredByHeader: false,
  turbopack: {
    // Resolve the committed mock garden outside this experiment's package.
    root: fileURLToPath(new URL("../../", import.meta.url)),
  },
};

export default config;
