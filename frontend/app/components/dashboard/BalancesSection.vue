<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { Layers, Users, Search } from "lucide-vue-next";
import VirtualClientList from "~/components/dashboard/VirtualClientList.vue";
import FilterBar from "~/components/dashboard/FilterBar.vue";
import SortDropdown from "~/components/dashboard/SortDropdown.vue";
import type { ClientBalance } from "~/types/client";

type SortKey = "total-desc" | "total-asc" | "name-asc" | "name-desc";

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
    (e: "client-click", value: { clientId: string; clientName: string }): void;
}>();

const filterRef = ref<InstanceType<typeof FilterBar> | null>(null);

const hasFilter = computed(() => props.filterQuery.trim().length > 0);
const isFiltered = computed(
    () =>
        hasFilter.value &&
        props.processedClients.length !== props.clients.length,
);

function setSortKey(k: SortKey) {
    emit("update:sort-key", k);
}

function setFilterQuery(v: string) {
    emit("update:filter-query", v);
}

function clearFilter() {
    setFilterQuery("");
    filterRef.value?.focus();
}

function handleClientClick(payload: { clientId: string; clientName: string }) {
    emit("client-click", payload);
}
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
                <div
                    v-if="props.grandTotal > 0"
                    class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#1a1a2e] text-white text-sm"
                    :aria-label="`Grand total: ${props.grandTotal} containers outstanding`"
                >
                    <Layers class="w-3.5 h-3.5" aria-hidden="true" />
                    <span>{{ props.grandTotal }} out</span>
                </div>

                <SortDropdown
                    v-if="props.clients.length > 1"
                    :sort-key="props.sortKey"
                    :sort-labels="props.sortLabels"
                    :disabled="props.clients.length <= 1"
                    @update:sortKey="(k) => setSortKey(k)"
                />
            </div>
        </div>

        <!-- Filter bar -->
        <div v-if="props.clients.length > 0" class="relative mb-3">
            <FilterBar
                ref="filterRef"
                :model-value="props.filterQuery"
                :placeholder="`Filter ${props.clients.length} client${props.clients.length !== 1 ? 's' : ''}…`"
                @update:modelValue="setFilterQuery"
            />
        </div>

        <!-- Filter hint -->
        <p
            v-if="isFiltered"
            class="text-xs text-[#717182] mb-2"
            aria-live="polite"
            aria-atomic="true"
        >
            Showing
            <strong class="text-[#1a1a2e]">{{
                props.processedClients.length
            }}</strong>
            of {{ props.clients.length }} clients
        </p>

        <!-- Empty: no clients at all -->
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

        <!-- Empty: filter has no matches -->
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

        <!-- Client list + footer -->
        <template v-else>
            <VirtualClientList
                :clients="props.processedClients"
                @client-click="handleClientClick"
            />

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
