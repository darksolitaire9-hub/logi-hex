// frontend/nuxt.config.ts
export default defineNuxtConfig({
  ssr: false, // Required for Tauri desktop packaging
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui", "@nuxtjs/i18n"],
  i18n: {
    locales: [
      { code: 'en', file: 'en.json', name: 'English' },
      { code: 'es', file: 'es.json', name: 'Español' },
      { code: 'ja', file: 'ja.json', name: '日本語' }
    ],
    defaultLocale: 'en',
    strategy: 'no_prefix',
    lazy: true,
    langDir: 'locales',
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
