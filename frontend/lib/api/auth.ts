// app/lib/api/auth.ts
import { $fetch } from "ofetch";

export async function loginApi(
  username: string,
  password: string,
): Promise<{ access_token: string; token_type: string }> {
  return await $fetch("/api/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username, password }),
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
}
