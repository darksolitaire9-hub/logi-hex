// frontend/nuxt.config.ts
const apiUrl = process.env.API_URL || "http://localhost:8000";

export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui"],
  css: ["~/assets/css/main.css"],
  runtimeConfig: {
    public: {
      apiBase: "/api",
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
