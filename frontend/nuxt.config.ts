// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui"],
  css: ["~/assets/css/main.css"],

  nitro: {
    routeRules: {
      // Forward all /api/** requests to FastAPI on port 8000
      "/api/**": {
        proxy: "http://localhost:8000/api/**",
      },
    },
  },
});
