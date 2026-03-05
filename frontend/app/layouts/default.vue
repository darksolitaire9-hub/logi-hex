<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref } from "vue";
import { useRoute } from "vue-router";
import { Package, Settings2, Layers, Search, Tags } from "lucide-vue-next";
import { Motion, AnimatePresence } from "motion-v";
import { useApp } from "~/composables/useApp";

import CommandPalette from "~/components/CommandPalette.vue";
import LogModal from "~/components/LogModal.vue";
import SuccessBanner from "~/components/SuccessBanner.vue";

const route = useRoute();
const { config } = useApp();

// State
const paletteOpen = ref(false);
const logModalDirection = ref<"OUT" | "IN" | null>(null);
const successInfo = ref<{ clientName: string; direction: "OUT" | "IN" } | null>(
    null,
);

// Global shortcut ⌘K / Ctrl+K
const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        paletteOpen.value = !paletteOpen.value;
    }
};

onMounted(() => {
    if (!import.meta.client) return;
    document.addEventListener("keydown", handler);
});
onBeforeUnmount(() => {
    if (!import.meta.client) return;
    document.removeEventListener("keydown", handler);
});

// Modal open callback (provided to children)
const openModal = (direction: "OUT" | "IN") => {
    logModalDirection.value = direction;
};

// Success handler
const handleSuccess = (clientName: string, direction: "OUT" | "IN") => {
    logModalDirection.value = null;
    successInfo.value = { clientName, direction };
};

// Provide to child pages (Nuxt equivalent of Outlet context)
provide("onOpenModal", openModal);

const navLinks = computed(() => [
    { to: "/", label: "Dashboard", icon: Layers },
    {
        to: "/primary",
        label: config.value.primaryCategoryName,
        icon: Package,
    },
    {
        to: "/content",
        label: config.value.contentCategoryName,
        icon: Tags,
    },
]);

const isMac = computed(() => {
    if (!import.meta.client) return false;
    return /Mac|iPhone|iPod|iPad/.test(navigator.platform);
});

const isActive = (to: string) => {
    if (to === "/") return route.path === "/";
    return route.path.startsWith(to);
};
</script>

<template>
    <div class="min-h-screen bg-[#f8f8fa] flex flex-col">
        <!-- Global overlays -->
        <CommandPalette
            :is-open="paletteOpen"
            @close="paletteOpen = false"
            @open-modal="openModal"
        />

        <LogModal
            v-if="logModalDirection"
            :direction="logModalDirection"
            @close="logModalDirection = null"
            @success="handleSuccess"
        />

        <!-- Header -->
        <header
            class="bg-white border-b border-[rgba(0,0,0,0.08)] sticky top-0 z-30"
        >
            <div
                class="max-w-[880px] mx-auto px-4 sm:px-6 h-14 flex items-center gap-3"
            >
                <!-- Brand -->
                <NuxtLink
                    to="/"
                    class="flex items-center gap-2 text-[#1a1a2e] hover:opacity-80 transition-opacity focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] rounded-md shrink-0"
                >
                    <div
                        class="w-7 h-7 rounded-lg bg-[#1a1a2e] flex items-center justify-center"
                    >
                        <span
                            class="text-white text-xs font-bold tracking-tight"
                            >LH</span
                        >
                    </div>
                    <span class="font-semibold text-[#1a1a2e] hidden sm:block"
                        >logi-hex</span
                    >
                </NuxtLink>

                <!-- Search trigger -->
                <button
                    @click="paletteOpen = true"
                    aria-label="Open command palette"
                    :aria-keyshortcuts="isMac ? 'Meta+k' : 'Control+k'"
                    class="flex-1 max-w-[280px] mx-auto flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[rgba(0,0,0,0.1)] bg-[#f8f8fa] hover:bg-[#f0f0f4] hover:border-[rgba(0,0,0,0.18)] transition-all text-sm text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] group"
                >
                    <Search
                        class="w-3.5 h-3.5 shrink-0 group-hover:text-[#717182] transition-colors"
                    />
                    <span class="flex-1 text-left hidden sm:block"
                        >Search…</span
                    >
                    <span class="hidden sm:flex items-center gap-0.5 shrink-0">
                        <kbd
                            class="px-1.5 py-0.5 rounded border border-[rgba(0,0,0,0.1)] text-[10px] text-[#c0c0cc] bg-white"
                        >
                            {{ isMac ? "⌘" : "Ctrl" }}
                        </kbd>
                        <kbd
                            class="px-1.5 py-0.5 rounded border border-[rgba(0,0,0,0.1)] text-[10px] text-[#c0c0cc] bg-white"
                        >
                            K
                        </kbd>
                    </span>
                </button>

                <!-- Navigation -->
                <nav class="flex items-center gap-1 shrink-0">
                    <NuxtLink
                        v-for="link in navLinks"
                        :key="link.to"
                        :to="link.to"
                        :class="[
                            'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e]',
                            isActive(link.to)
                                ? 'bg-[#1a1a2e] text-white'
                                : 'text-[#717182] hover:text-[#1a1a2e] hover:bg-[#f0f0f4]',
                        ]"
                    >
                        <component :is="link.icon" class="w-4 h-4" />
                        <span class="hidden md:block">{{ link.label }}</span>
                    </NuxtLink>
                </nav>

                <!-- Setup -->
                <NuxtLink
                    to="/settings"
                    :class="[
                        'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] shrink-0',
                        route.path === '/settings'
                            ? 'bg-[#1a1a2e] text-white'
                            : 'text-[#717182] hover:text-[#1a1a2e] hover:bg-[#f0f0f4]',
                    ]"
                >
                    <Settings2 class="w-4 h-4" />
                    <span class="hidden md:block">Settings</span>
                </NuxtLink>
            </div>
        </header>

        <!-- Page content -->
        <main class="flex-1 max-w-[880px] w-full mx-auto px-4 sm:px-6 py-6">
            <!-- ✅ Presence -> AnimatePresence (Presence is not exported) -->
            <AnimatePresence>
                <Motion
                    v-if="successInfo"
                    :initial="{ opacity: 0, y: -10 }"
                    :animate="{ opacity: 1, y: 0 }"
                    :exit="{ opacity: 0, y: -10 }"
                >
                    <SuccessBanner
                        :client-name="successInfo.clientName"
                        :direction="successInfo.direction"
                        @dismiss="successInfo = null"
                    />
                </Motion>
            </AnimatePresence>

            <!-- ✅ Nuxt page outlet (not RouterView) -->
            <NuxtPage />
        </main>

        <footer
            class="border-t border-[rgba(0,0,0,0.06)] py-4 text-center text-xs text-[#a0a0b0]"
        >
            logi-hex · Container Tracking
        </footer>
    </div>
</template>
