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
      { code: 'ja', files: ['ja/core.json', 'ja/inventory.json', 'ja/login.json', 'ja/errors.json'], name: '日本語' },
      { code: 'pt-PT', files: ['pt-PT/core.json', 'pt-PT/inventory.json', 'pt-PT/login.json', 'pt-PT/errors.json'], name: 'Português (PT)' },
      { code: 'pt-BR', files: ['pt-BR/core.json', 'pt-BR/inventory.json', 'pt-BR/login.json', 'pt-BR/errors.json'], name: 'Português (BR)' },
      { code: 'de', files: ['de/core.json', 'de/inventory.json', 'de/login.json', 'de/errors.json'], name: 'Deutsch' },
      { code: 'nl', files: ['nl/core.json', 'nl/inventory.json', 'nl/login.json', 'nl/errors.json'], name: 'Nederlands' },
      { code: 'hi', files: ['hi/core.json', 'hi/inventory.json', 'hi/login.json', 'hi/errors.json'], name: 'हिन्दी' },
      { code: 'ne', files: ['ne/core.json', 'ne/inventory.json', 'ne/login.json', 'ne/errors.json'], name: 'नेपाली' }
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
