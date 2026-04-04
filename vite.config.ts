import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ command }) => ({
  publicDir: command === "serve" ? "output" : false,
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  build: {
    outDir: "static/dist",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "bundle.js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith(".css")) return "bundle.css";
          return "[name][extname]";
        },
      },
    },
  },
}));
