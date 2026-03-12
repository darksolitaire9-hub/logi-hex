// frontend/nuxt.config.ts
const apiUrl = process.env.API_URL || "http://localhost:8000";

export default defineNuxtConfig({
  ssr: false,
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui"],
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    public: {
      API_URL: process.env.NUXT_PUBLIC_API_URL ?? "http://localhost:8000", // default
    },
  },
  nitro: {
    routeRules: {
      "/api/**": {
        proxy: `${apiUrl}/api/**`,
      },
    },
  },
});
