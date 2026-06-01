// frontend/nuxt.config.ts
export default defineNuxtConfig({
  ssr: false, // Required for Tauri desktop packaging
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui", "@nuxtjs/i18n"],
  i18n: {
    restructureDir: false,
    locales: [
      { code: 'en', files: ['en/core.json', 'en/inventory.json', 'en/login.json', 'en/errors.json'], name: 'English' },
      { code: 'es', files: ['es/core.json', 'es/inventory.json', 'es/login.json', 'es/errors.json'], name: 'Español' },
      { code: 'ja', files: ['ja/core.json', 'ja/inventory.json', 'ja/login.json', 'ja/errors.json'], name: '日本語' }
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
