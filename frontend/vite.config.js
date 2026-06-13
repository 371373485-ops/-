import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  server: {
    allowedHosts: [".trycloudflare.com", ".ngrok-free.app"],
    port: 5173,
  },
});
