import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
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
});
