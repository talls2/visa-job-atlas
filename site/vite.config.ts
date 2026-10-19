import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// BASE_PATH is set by the GitHub Pages workflow (e.g. "/visa-job-atlas/").
export default defineConfig({
  base: process.env.BASE_PATH || "/",
  plugins: [react()],
  server: { fs: { allow: [".."] } },
  build: { target: "es2020", chunkSizeWarningLimit: 1500 },
});
