import { useAuth } from "~/composables/useAuth";

export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated } = useAuth();

  // If not authenticated, send to login (except when already there)
  if (!isAuthenticated.value && to.path !== "/login") {
    return navigateTo("/login");
  }

  // If authenticated and trying to go to /login, send to home
  if (isAuthenticated.value && to.path === "/login") {
    return navigateTo("/");
  }

  // No setup/config guard for now — workspace picker lives at /setup
});
