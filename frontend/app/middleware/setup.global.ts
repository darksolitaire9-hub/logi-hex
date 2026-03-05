export default defineNuxtRouteMiddleware((to) => {
  const { config } = useApp();

  const isSetupComplete = config.value.isSetupComplete;
  const isSetupRoute = to.path === "/setup";
  const isSettingsRoute = to.path === "/settings";

  if (!isSetupComplete && !isSetupRoute) {
    return navigateTo("/setup");
  }

  if (isSetupComplete && isSetupRoute) {
    return navigateTo("/settings"); // ← was "/"
  }
});
