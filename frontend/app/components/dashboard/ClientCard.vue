<script setup lang="ts">
import type { ClientBalance } from "~/types/client";

const props = defineProps<{
    client: ClientBalance;
}>();

const emit = defineEmits<{
    (e: "client-click", value: { clientId: string; clientName: string }): void;
}>();
</script>

<template>
    <button
        type="button"
        @click="
            emit('client-click', {
                clientId: props.client.clientId,
                clientName: props.client.clientName,
            })
        "
        :aria-label="`View transactions for ${props.client.clientName}`"
        class="w-full text-left px-4 py-3 rounded-xl bg-white border border-[rgba(0,0,0,0.08)] hover:border-[rgba(0,0,0,0.18)] hover:shadow-sm active:scale-[0.99] transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e]"
    >
        <div class="flex items-center justify-between gap-3 mb-2">
            <span class="font-medium text-[#1a1a2e] text-sm truncate">
                {{ props.client.clientName }}
            </span>
            <span
                class="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#1a1a2e] text-white text-xs font-semibold"
            >
                {{ props.client.total }} out
            </span>
        </div>
        <div class="flex flex-wrap gap-1.5">
            <span
                v-for="item in props.client.items"
                :key="item.itemId"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#f0f0f4] text-xs text-[#717182]"
            >
                {{ item.label }}
                <span class="font-semibold text-[#1a1a2e]"
                    >× {{ item.quantity }}</span
                >
            </span>
        </div>
    </button>
</template>
