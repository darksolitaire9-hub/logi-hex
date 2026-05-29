// frontend/nuxt.config.ts
export default defineNuxtConfig({
  ssr: false, // Required for Tauri desktop packaging
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui"],
  css: ["~/assets/css/main.css"],

  // Optional: Optimize for desktop delivery
  vite: {
    clearScreen: false,
    envPrefix: ['VITE_', 'TAURI_'],
    server: {
      strictPort: true,
    },
  },
});
