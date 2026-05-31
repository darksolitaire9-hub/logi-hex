// frontend/nuxt.config.ts
export default defineNuxtConfig({
  ssr: false, // Required for Tauri desktop packaging
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui", "@nuxtjs/i18n"],
  i18n: {
    restructureDir: false,
    locales: [
      { code: 'en', files: ['en/core.json', 'en/inventory.json'], name: 'English' },
      // Other languages would replicate this split structure
    ],
    defaultLocale: 'en',
    strategy: 'no_prefix',
    lazy: true,
    langDir: '../locales/',
    types: 'composition',
    defaultDirection: 'auto',
    vueI18n: './i18n.config.ts'
  },
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
