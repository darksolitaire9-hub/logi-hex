import { $fetch } from "ofetch";

export function useApiClient() {
  const { getToken, clearToken } = useAuth();
  const config = useRuntimeConfig();

  const baseURL = config.public.API_URL as string;

  return $fetch.create({
    baseURL,

    async onRequest({ options: reqOptions }) {
      const token = getToken();
      const headers = new Headers(reqOptions.headers || {});

      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }

      reqOptions.headers = headers;
    },

    async onResponseError({ response }) {
      if (response.status === 401) {
        clearToken();
        await navigateTo("/login");
      }
    },
  });
}
