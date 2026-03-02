<script setup lang="ts">
import { computed } from "vue";
import {
    ArrowUpRight,
    ArrowDownLeft,
    Package,
    Settings2,
} from "lucide-vue-next";

const props = defineProps<{
    primaryLabel: string;
    contentLabel?: string | null;
}>();

const emit = defineEmits<{
    (e: "open-modal", direction: "OUT" | "IN"): void;
}>();

const todayISO = computed(() => new Date().toISOString().slice(0, 10));
const todayLabel = computed(() =>
    new Date().toLocaleDateString("en-GB", {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
    }),
);
</script>

<template>
    <section aria-labelledby="today-heading">
        <div class="flex items-center justify-between mb-4">
            <h1 id="today-heading" class="text-[#1a1a2e]">Today</h1>
            <time class="text-sm text-[#717182]" :dateTime="todayISO">{{
                todayLabel
            }}</time>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
            <button
                @click="emit('open-modal', 'OUT')"
                class="group flex items-center gap-3 px-5 py-4 rounded-xl bg-[#ea580c] hover:bg-[#c2410c] active:bg-[#9a3412] text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ea580c] focus-visible:ring-offset-2 shadow-sm"
            >
                <div
                    class="w-9 h-9 rounded-lg bg-white/20 flex items-center justify-center shrink-0"
                >
                    <ArrowUpRight class="w-5 h-5" aria-hidden="true" />
                </div>
                <div class="text-left">
                    <div class="font-semibold">Issue OUT</div>
                    <div class="text-sm opacity-80">
                        Send containers to client
                    </div>
                </div>
            </button>

            <button
                @click="emit('open-modal', 'IN')"
                class="group flex items-center gap-3 px-5 py-4 rounded-xl bg-[#16a34a] hover:bg-[#15803d] active:bg-[#166534] text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#16a34a] focus-visible:ring-offset-2 shadow-sm"
            >
                <div
                    class="w-9 h-9 rounded-lg bg-white/20 flex items-center justify-center shrink-0"
                >
                    <ArrowDownLeft class="w-5 h-5" aria-hidden="true" />
                </div>
                <div class="text-left">
                    <div class="font-semibold">Receive IN</div>
                    <div class="text-sm opacity-80">
                        Accept returned containers
                    </div>
                </div>
            </button>
        </div>

        <div class="flex flex-wrap gap-2">
            <NuxtLink
                to="/primary"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-[rgba(0,0,0,0.1)] text-sm text-[#717182] hover:text-[#1a1a2e] hover:border-[rgba(0,0,0,0.2)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e]"
            >
                <Package class="w-3.5 h-3.5" aria-hidden="true" />
                Manage {{ props.primaryLabel }}
            </NuxtLink>

            <NuxtLink
                v-if="props.contentLabel"
                to="/content"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-[rgba(0,0,0,0.1)] text-sm text-[#717182] hover:text-[#1a1a2e] hover:border-[rgba(0,0,0,0.2)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e]"
            >
                <Settings2 class="w-3.5 h-3.5" aria-hidden="true" />
                Manage {{ props.contentLabel }}
            </NuxtLink>
        </div>
    </section>
</template>
