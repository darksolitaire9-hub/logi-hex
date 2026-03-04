// frontend/app/middleware/setup.global.ts
export default defineNuxtRouteMiddleware((to) => {
  const { config } = useApp();

  const isSetupComplete = config.value.isSetupComplete;
  const isSetupRoute = to.path === "/setup";

  if (!isSetupComplete && !isSetupRoute) {
    return navigateTo("/setup");
  }

  if (isSetupComplete && isSetupRoute) {
    return navigateTo("/");
  }
});
