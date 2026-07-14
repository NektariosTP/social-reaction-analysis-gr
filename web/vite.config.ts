import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // The project keeps one .env at the repo root (shared with the Python
  // services) instead of a separate web/.env — read VITE_* vars from there.
  envDir: "../",
  server: {
    port: 5173,
  },
});
