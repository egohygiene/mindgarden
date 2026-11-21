import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../src/mindgarden/interfaces/web/studio",
    emptyOutDir: true,
    manifest: true,
    license: true,
    // Three is downloaded only when a reader switches the graph to 3D.
    chunkSizeWarningLimit: 1000,
  },
});
