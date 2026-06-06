// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // During dev: proxy API calls to the FastAPI backend
      "/predict":    { target: "http://localhost:8000", changeOrigin: true },
      "/health":     { target: "http://localhost:8000", changeOrigin: true },
      "/model-info": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
