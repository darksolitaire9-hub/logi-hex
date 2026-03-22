<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref } from "vue";
import { useRoute } from "vue-router";
import { Package, Settings2, Layers, Search, Tags } from "lucide-vue-next";
import { Motion, AnimatePresence } from "motion-v";

import CommandPalette from "~/components/palette/CommandPalette.vue";
import LogModal from "~/components/log/LogModal.vue";
import SuccessBanner from "~/components/common/SuccessBanner.vue";

// Removed: useApp, useConfig

const route = useRoute();

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

// Provide to child pages
provide("onOpenModal", openModal);

// TEMP nav labels until we have new dashboards
const navLinks = computed(() => [
    { to: "/", label: "Dashboard", icon: Layers },
    { to: "/setup", label: "Setup", icon: Package },
    { to: "/workspaces", label: "Workspaces", icon: Tags },
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
