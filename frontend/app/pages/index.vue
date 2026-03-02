<script setup lang="ts">
import { computed, inject, ref } from "vue";
import { useApp } from "~/composables/useApp";
import TodaySection from "~/components/dashboard/TodaySection.vue";
import BalancesSection from "~/components/dashboard/BalancesSection.vue";

type SortKey = "total-desc" | "total-asc" | "name-asc" | "name-desc";

const SORT_LABELS: Record<SortKey, string> = {
    "total-desc": "Most out",
    "total-asc": "Fewest out",
    "name-asc": "A → Z",
    "name-desc": "Z → A",
};

const { config, clientBalances, grandTotal } = useApp();

const onOpenModal =
    inject<(direction: "OUT" | "IN") => void>("onOpenModal") ?? (() => {});

const filterQuery = ref("");
const sortKey = ref<SortKey>("total-desc");

const processedClients = computed(() => {
    const clients = clientBalances.value;
    const q = filterQuery.value.trim().toLowerCase();
    const filtered = q
        ? clients.filter((c) => c.clientName.toLowerCase().includes(q))
        : clients;

    return [...filtered].sort((a, b) => {
        switch (sortKey.value) {
            case "total-desc":
                return b.total - a.total;
            case "total-asc":
                return a.total - b.total;
            case "name-asc":
                return a.clientName.localeCompare(b.clientName);
            case "name-desc":
                return b.clientName.localeCompare(a.clientName);
        }
    });
});

const filteredTotal = computed(() =>
    processedClients.value.reduce((s, c) => s + c.total, 0),
);
</script>

<template>
    <TodaySection
        :primary-label="config?.primaryCategoryName ?? 'Primary'"
        :content-label="config?.contentCategoryName ?? 'Content'"
        @open-modal="onOpenModal"
    />

    <div class="my-6 border-t border-[rgba(0,0,0,0.06)]" />

    <BalancesSection
        :clients="clientBalances"
        :processed-clients="processedClients"
        :grand-total="grandTotal"
        :filtered-total="filteredTotal"
        :sort-key="sortKey"
        :sort-labels="SORT_LABELS"
        :filter-query="filterQuery"
        @update:sort-key="(k) => (sortKey = k)"
        @update:filter-query="(q) => (filterQuery = q)"
    />
</template>
