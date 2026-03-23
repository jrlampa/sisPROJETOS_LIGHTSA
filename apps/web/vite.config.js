import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";

const versionFile = path.resolve(__dirname, "..", "..", "VERSION");
const appVersion = fs.existsSync(versionFile) ? fs.readFileSync(versionFile, "utf-8").trim() : "0.0.0";

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion || "0.0.0"),
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
        },
      },
    },
  },
});
