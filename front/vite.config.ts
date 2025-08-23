import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
// import { componentTagger } from "lovable-tagger"; // Désactivé pour diagnostiquer boucle import / stack overflow

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
  plugins: [
    react(),
    // NOTE: Le plugin lovable-tagger semble provoquer une récursion infinie ("Maximum call stack size exceeded").
    // Pour réactiver après diagnostic : décommentez l'import et la ligne ci-dessous.
    // mode === 'development' && componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
