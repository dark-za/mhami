import { defineConfig } from "vite";

export default defineConfig({
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        if (warning.code === "MODULE_LEVEL_DIRECTIVE") {
          return;
        }
        warn(warning);
      },
    },
  },
  server: {
    host: "0.0.0.0",
    // Docker Desktop bind mounts on Windows and macOS do not always emit
    // filesystem events into the Linux container. Enable polling only for
    // the development compose override so source edits reliably reach Vite.
    watch: process.env.VITE_DOCKER_WATCH === "true" ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET ?? "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
