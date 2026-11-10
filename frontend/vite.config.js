import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      "/events": "http://localhost:8080",
      "/loserCounts": "http://localhost:8080",
    },
  },
});
