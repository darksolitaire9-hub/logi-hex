<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
    Layers,
    Users,
    Search,
    X,
    ArrowDownUp,
    ChevronDown,
} from "lucide-vue-next";
import VirtualClientList from "~/components/VirtualClientList.vue";
import { AnimatePresence, Motion } from "motion-v";

type SortKey = "total-desc" | "total-asc" | "name-asc" | "name-desc";

type ClientBalance = {
    clientName: string;
    total: number;
    items: Array<{ itemId: string | number; label: string; quantity: number }>;
};

const props = defineProps<{
    clients: ClientBalance[];
    processedClients: ClientBalance[];
    grandTotal: number;
    filteredTotal: number;
    sortKey: SortKey;
    sortLabels: Record<SortKey, string>;
    filterQuery: string;
}>();

const emit = defineEmits<{
    (e: "update:sort-key", value: SortKey): void;
    (e: "update:filter-query", value: string): void;
}>();

const isClient = import.meta.client;

const sortOpen = ref(false);
const sortRef = ref<HTMLDivElement | null>(null);
const filterRef = ref<HTMLInputElement | null>(null);

const hasFilter = computed(() => props.filterQuery.trim().length > 0);
const isFiltered = computed(
    () =>
        hasFilter.value &&
        props.processedClients.length !== props.clients.length,
);

function setSortKey(k: SortKey) {
    emit("update:sort-key", k);
    sortOpen.value = false;
}

function setFilterQuery(v: string) {
    emit("update:filter-query", v);
}

function clearFilter() {
    setFilterQuery("");
    filterRef.value?.focus();
}

const onOutsideMouseDown = (e: MouseEvent) => {
    const root = sortRef.value;
    if (root && !root.contains(e.target as Node)) sortOpen.value = false;
};

watch(sortOpen, (open) => {
    if (!isClient) return;
    if (open) document.addEventListener("mousedown", onOutsideMouseDown);
    else document.removeEventListener("mousedown", onOutsideMouseDown);
});

onBeforeUnmount(() => {
    if (!isClient) return;
    document.removeEventListener("mousedown", onOutsideMouseDown);
});
</script>

<template>
    <section aria-labelledby="balances-heading">
        <!-- Header row -->
        <div class="flex items-center justify-between gap-3 mb-3">
            <h2
                id="balances-heading"
                class="text-[#1a1a2e] flex items-center gap-2 shrink-0"
            >
                <Users class="w-5 h-5 text-[#717182]" aria-hidden="true" />
                Who has what
            </h2>

            <div class="flex items-center gap-2">
                <!-- Grand total badge -->
                <div
                    v-if="props.grandTotal > 0"
                    class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1a1a2e] text-white text-sm"
                    :aria-label="`Grand total: ${props.grandTotal} containers outstanding`"
                >
                    <Layers class="w-3.5 h-3.5" aria-hidden="true" />
                    <span>{{ props.grandTotal }} out</span>
                </div>

                <!-- Sort dropdown -->
                <div
                    v-if="props.clients.length > 1"
                    class="relative"
                    ref="sortRef"
                >
                    <button
                        @click="sortOpen = !sortOpen"
                        :aria-label="`Sort: ${props.sortLabels[props.sortKey]}`"
                        :aria-expanded="sortOpen"
                        aria-haspopup="listbox"
                        class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[rgba(0,0,0,0.1)] bg-white hover:bg-[#f0f0f4] text-sm text-[#717182] hover:text-[#1a1a2e] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e]"
                    >
                        <ArrowDownUp class="w-3.5 h-3.5" aria-hidden="true" />
                        <span class="hidden sm:block">{{
                            props.sortLabels[props.sortKey]
                        }}</span>
                        <ChevronDown
                            class="w-3 h-3 transition-transform"
                            :class="sortOpen ? 'rotate-180' : ''"
                            aria-hidden="true"
                        />
                    </button>

                    <!-- AnimatePresence stays mounted; v-if goes on Motion child. -->
                    <AnimatePresence>
                        <Motion
                            v-if="sortOpen"
                            :initial="{ opacity: 0, y: -6, scale: 0.97 }"
                            :animate="{ opacity: 1, y: 0, scale: 1 }"
                            :exit="{ opacity: 0, y: -4, scale: 0.97 }"
                            :transition="{ duration: 0.12 }"
                            as="ul"
                            role="listbox"
                            aria-label="Sort options"
                            class="absolute right-0 top-full mt-1.5 w-40 bg-white border border-[rgba(0,0,0,0.1)] rounded-xl shadow-lg overflow-hidden z-20 py-1"
                        >
                            <li
                                v-for="key in Object.keys(
                                    props.sortLabels,
                                ) as SortKey[]"
                                :key="key"
                                role="option"
                                :aria-selected="props.sortKey === key"
                                @click="setSortKey(key)"
                                class="flex items-center justify-between px-3 py-2 text-sm cursor-pointer transition-colors"
                                :class="
                                    props.sortKey === key
                                        ? 'bg-[#f0f0f4] text-[#1a1a2e] font-medium'
                                        : 'text-[#717182] hover:bg-[#f8f8fa] hover:text-[#1a1a2e]'
                                "
                            >
                                {{ props.sortLabels[key] }}
                                <span
                                    v-if="props.sortKey === key"
                                    class="w-1.5 h-1.5 rounded-full bg-[#1a1a2e]"
                                    aria-hidden="true"
                                />
                            </li>
                        </Motion>
                    </AnimatePresence>
                </div>
            </div>
        </div>

        <!-- Filter bar -->
        <div v-if="props.clients.length > 0" class="relative mb-3">
            <Search
                class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#a0a0b0] pointer-events-none"
                aria-hidden="true"
            />
            <input
                ref="filterRef"
                type="search"
                :value="props.filterQuery"
                @input="
                    setFilterQuery(($event.target as HTMLInputElement).value)
                "
                :placeholder="`Filter ${props.clients.length} client${props.clients.length !== 1 ? 's' : ''}…`"
                aria-label="Filter clients"
                class="w-full pl-8 pr-8 py-2 rounded-lg border border-[rgba(0,0,0,0.1)] bg-white text-sm text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors hover:border-[rgba(0,0,0,0.18)]"
            />
            <button
                v-if="hasFilter"
                @click="clearFilter"
                aria-label="Clear filter"
                class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#a0a0b0] hover:text-[#1a1a2e] transition-colors"
            >
                <X class="w-3.5 h-3.5" />
            </button>
        </div>

        <!-- Filter hint -->
        <p
            v-if="isFiltered"
            class="text-xs text-[#717182] mb-2"
            aria-live="polite"
            aria-atomic="true"
        >
            Showing
            <strong className="text-[#1a1a2e]">{{
                props.processedClients.length
            }}</strong>
            of {{ props.clients.length }} clients
        </p>

        <!-- Empty states / list -->
        <div
            v-if="props.clients.length === 0"
            class="flex flex-col items-center justify-center py-16 text-center"
        >
            <div
                class="w-16 h-16 rounded-2xl bg-[#f0f0f4] flex items-center justify-center mb-4"
            >
                <Layers class="w-8 h-8 text-[#a0a0b0]" aria-hidden="true" />
            </div>
            <h3 class="text-[#1a1a2e] mb-1">All clear!</h3>
            <p class="text-sm text-[#717182] max-w-xs">
                No outstanding containers. Issue some to clients to start
                tracking.
            </p>
        </div>

        <div
            v-else-if="props.processedClients.length === 0"
            class="flex flex-col items-center justify-center py-12 text-center"
        >
            <div
                class="w-12 h-12 rounded-2xl bg-[#f0f0f4] flex items-center justify-center mb-3"
            >
                <Search class="w-6 h-6 text-[#a0a0b0]" aria-hidden="true" />
            </div>
            <p class="text-sm text-[#717182]">
                No client matches
                <strong class="text-[#1a1a2e]"
                    >"{{ props.filterQuery }}"</strong
                >
            </p>
            <button
                @click="setFilterQuery('')"
                class="mt-2 text-xs text-[#1a1a2e] underline underline-offset-2 hover:opacity-70 transition-opacity"
            >
                Clear filter
            </button>
        </div>

        <template v-else>
            <VirtualClientList :clients="props.processedClients" />

            <div
                class="mt-3 bg-[#f0f0f4] rounded-xl px-4 py-3 flex items-center justify-between"
            >
                <span class="text-sm text-[#717182]">
                    {{
                        isFiltered
                            ? `${props.processedClients.length} of ${props.clients.length} clients shown`
                            : "Grand total outstanding"
                    }}
                </span>
                <span class="font-semibold text-[#1a1a2e]" aria-live="polite">
                    {{ props.filteredTotal }} containers
                </span>
            </div>
        </template>
    </section>
</template>
