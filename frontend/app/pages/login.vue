<script setup lang="ts">
import { ref, nextTick } from "vue";
import { loginApi } from "../../lib/api/auth";

definePageMeta({ layout: "setup" });

const { isAuthenticated, setToken } = useAuth();

if (isAuthenticated.value) {
    await navigateTo("/");
}

const username = ref("");
const password = ref("");
const error = ref<string | null>(null);
const loading = ref(false);

async function handleLogin() {
    error.value = null;
    loading.value = true;
    try {
        const data = await loginApi(username.value, password.value);
        setToken(data.access_token);
        await nextTick();
        await navigateTo("/", { replace: true });
    } catch (e: any) {
        const status = e?.status ?? e?.response?.status;
        if (status === 401) {
            error.value = "Invalid credentials. Please try again.";
        } else {
            error.value = "Cannot reach the server. Is the backend running?";
        }
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div
        class="w-full max-w-sm mx-auto bg-white rounded-2xl shadow-2xl overflow-hidden"
    >
        <div class="bg-[#1a1a2e] px-6 py-5">
            <h1 class="text-xl font-semibold text-white">logi-hex</h1>
            <p class="text-sm text-white/60 mt-0.5">Sign in to continue</p>
        </div>

        <form
            class="px-6 py-6 flex flex-col gap-5"
            @submit.prevent="handleLogin"
            novalidate
        >
            <div
                v-if="error"
                role="alert"
                class="bg-[#fff7ed] border border-[#fed7aa] rounded-lg px-4 py-3 text-sm font-medium text-[#9a3412]"
            >
                {{ error }}
            </div>

            <div>
                <label
                    for="username"
                    class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                >
                    Username
                </label>
                <input
                    id="username"
                    v-model="username"
                    type="text"
                    autocomplete="username"
                    placeholder="username"
                    :disabled="loading"
                    class="w-full px-3 py-2.5 rounded-lg border border-[rgba(0,0,0,0.15)] bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors disabled:opacity-50"
                />
            </div>

            <div>
                <label
                    for="password"
                    class="block text-sm font-medium text-[#1a1a2e] mb-1.5"
                >
                    Password
                </label>
                <input
                    id="password"
                    v-model="password"
                    type="password"
                    autocomplete="current-password"
                    placeholder="••••••••"
                    :disabled="loading"
                    class="w-full px-3 py-2.5 rounded-lg border border-[rgba(0,0,0,0.15)] bg-white text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors disabled:opacity-50"
                />
            </div>

            <button
                type="submit"
                :disabled="loading"
                class="w-full px-6 py-2.5 rounded-lg bg-[#1a1a2e] hover:bg-[#2d2d4e] active:bg-[#0f0f1e] text-white text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] focus-visible:ring-offset-2 disabled:opacity-60 flex items-center justify-center gap-2"
            >
                <svg
                    v-if="loading"
                    class="w-4 h-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                >
                    ircle class="opacity-25" cx="12" cy="12" r="10"
                    stroke="currentColor" stroke-width="4"/>
                    <path
                        class="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8z"
                    />
                </svg>
                {{ loading ? "Signing in…" : "Sign in" }}
            </button>
        </form>
    </div>
</template>
