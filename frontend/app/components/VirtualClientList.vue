<script setup lang="ts">
import { computed, ref } from "vue";
import { useVirtualizer } from "@tanstack/vue-virtual";
import ClientCard from "~/components/ClientCard.vue";

type ClientBalance = {
    clientName: string;
    total: number;
    items: Array<{ itemId: string | number; label: string; quantity: number }>;
};

const props = defineProps<{
    clients: ClientBalance[];
}>();

const parentRef = ref<HTMLDivElement | null>(null);

const virtualizerOptions = computed(() => ({
    count: props.clients.length,
    getScrollElement: () => parentRef.value,
    estimateSize: (i: number) => {
        const chipCount = props.clients[i]?.items.length ?? 1;
        const chipRows = Math.ceil(chipCount / 4);
        return 72 + chipRows * 28;
    },
    overscan: 6,
    gap: 12,
}));

const virtualizer = useVirtualizer(virtualizerOptions);

const virtualItems = computed(() => virtualizer.value.getVirtualItems());
const totalSize = computed(() => virtualizer.value.getTotalSize());

const measureEl = (el: Element | null) => {
    if (!el) return;
    virtualizer.value.measureElement(el as HTMLElement);
};
</script>

<template>
    <div
        ref="parentRef"
        class="overflow-y-auto rounded-xl [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-[rgba(0,0,0,0.15)] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb:hover]:bg-[rgba(0,0,0,0.28)]"
        :style="{
            maxHeight: 'min(600px, calc(100vh - 340px))',
            minHeight: '120px',
        }"
        role="list"
        aria-label="Client balances"
        tabindex="0"
    >
        <div :style="{ height: `${totalSize}px`, position: 'relative' }">
            <div
                v-for="vItem in virtualItems"
                :key="vItem.key"
                :data-index="vItem.index"
                :ref="measureEl"
                :style="{
                    position: 'absolute',
                    top: '0',
                    left: '0',
                    right: '0',
                    transform: `translateY(${vItem.start}px)`,
                }"
                role="listitem"
            >
                <ClientCard :client="props.clients[vItem.index]!" />
            </div>
        </div>
    </div>
</template>
