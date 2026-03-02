<script setup lang="ts">
type ClientBalance = {
    clientName: string;
    total: number;
    items: Array<{ itemId: string | number; label: string; quantity: number }>;
};

defineProps<{
    client: ClientBalance;
}>();
</script>

<template>
    <div
        class="bg-white rounded-xl border border-[rgba(0,0,0,0.08)] px-4 py-3.5 flex items-start gap-3 shadow-sm"
    >
        <div
            class="w-9 h-9 rounded-full bg-[#f0f0f4] flex items-center justify-center shrink-0 mt-0.5"
            aria-hidden="true"
        >
            <span class="text-sm font-semibold text-[#717182]">
                {{ client.clientName.slice(0, 1).toUpperCase() }}
            </span>
        </div>

        <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2 mb-2">
                <span class="text-[#1a1a2e] truncate font-medium">{{
                    client.clientName
                }}</span>
                <span
                    class="shrink-0 px-2 py-0.5 rounded-full bg-[#1a1a2e] text-white text-xs font-semibold"
                    :aria-label="`${client.total} containers outstanding`"
                >
                    {{ client.total }}
                </span>
            </div>

            <div class="flex flex-wrap gap-1.5">
                <span
                    v-for="item in client.items"
                    :key="item.itemId"
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#f8f8fa] border border-[rgba(0,0,0,0.08)] text-xs text-[#1a1a2e]"
                >
                    <span class="font-semibold">{{ item.quantity }}</span>
                    <span class="text-[#717182]">{{ item.label }}</span>
                </span>
            </div>
        </div>
    </div>
</template>
