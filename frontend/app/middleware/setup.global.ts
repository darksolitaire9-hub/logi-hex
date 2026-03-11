export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated } = useAuth();

  // Auth guard
  if (!isAuthenticated.value && to.path !== "/login") {
    return navigateTo("/login");
  }
  if (isAuthenticated.value && to.path === "/login") {
    return navigateTo("/");
  }

  // Stop here for unauthenticated users — don't run setup logic
  if (!isAuthenticated.value) {
    return;
  }

  // Setup guard — only for authenticated users
  const { config } = useApp();
  const isSetupComplete = config.value.isSetupComplete;
  const isSetupRoute = to.path === "/setup";

  if (!isSetupComplete && !isSetupRoute) {
    return navigateTo("/setup");
  }
  if (isSetupComplete && isSetupRoute) {
    return navigateTo("/settings");
  }
});
