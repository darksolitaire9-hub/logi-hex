// app/composables/useApiClient.ts
import { $fetch } from "ofetch";

export function useApiClient() {
  const { getToken, clearToken } = useAuth();
  const token = getToken();

  return $fetch.create({
    baseURL: "http://localhost:8000",
    credentials: "include",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    async onResponseError({ response }) {
      if (response.status === 401) {
        clearToken();
        await navigateTo("/login");
      }
    },
  });
}
