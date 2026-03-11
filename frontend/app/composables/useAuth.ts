// app/composables/useAuth.ts
import { ref, computed } from "vue";

const TOKEN_KEY = "logi-hex-token";

// Module-level — shared across all calls, same pattern as useConfig.ts
const token = ref<string | null>(
  import.meta.client ? localStorage.getItem(TOKEN_KEY) : null,
);

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value);

  function setToken(t: string) {
    token.value = t;
    if (import.meta.client) {
      localStorage.setItem(TOKEN_KEY, t);
    }
  }

  function clearToken() {
    token.value = null;
    if (import.meta.client) {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  function getToken(): string | null {
    return token.value;
  }

  return { isAuthenticated, setToken, clearToken, getToken };
}
