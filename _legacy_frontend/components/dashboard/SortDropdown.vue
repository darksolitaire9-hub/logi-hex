<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { ArrowDownUp, ChevronDown } from "lucide-vue-next";
import { AnimatePresence, Motion } from "motion-v";

type SortKey = "total-desc" | "total-asc" | "name-asc" | "name-desc";

const props = defineProps<{
    sortKey: SortKey;
    sortLabels: Record<SortKey, string>;
    disabled?: boolean;
}>();

const emit = defineEmits<{
    (e: "update:sortKey", value: SortKey): void;
}>();

const isClient = import.meta.client;

const open = ref(false);
const rootRef = ref<HTMLDivElement | null>(null);

function setKey(k: SortKey) {
    emit("update:sortKey", k);
    open.value = false;
}

const onOutsideMouseDown = (e: MouseEvent) => {
    const root = rootRef.value;
    if (root && !root.contains(e.target as Node)) open.value = false;
};

watch(open, (v) => {
    if (!isClient) return;
    if (v) document.addEventListener("mousedown", onOutsideMouseDown);
    else document.removeEventListener("mousedown", onOutsideMouseDown);
});

onBeforeUnmount(() => {
    if (!isClient) return;
    document.removeEventListener("mousedown", onOutsideMouseDown);
});
</script>

<template>
    <div class="relative" ref="rootRef">
        <button
            type="button"
            :disabled="props.disabled"
            @click="open = !open"
            :aria-label="`Sort: ${props.sortLabels[props.sortKey]}`"
            :aria-expanded="open"
            aria-haspopup="listbox"
            class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[rgba(0,0,0,0.1)] bg-white hover:bg-[#f0f0f4] text-sm text-[#717182] hover:text-[#1a1a2e] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] disabled:opacity-60 disabled:hover:bg-white"
        >
            <ArrowDownUp class="w-3.5 h-3.5" aria-hidden="true" />
            <span class="hidden sm:block">{{
                props.sortLabels[props.sortKey]
            }}</span>
            <ChevronDown
                class="w-3 h-3 transition-transform"
                :class="open ? 'rotate-180' : ''"
                aria-hidden="true"
            />
        </button>

        <AnimatePresence>
            <Motion
                v-if="open"
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
                    v-for="key in Object.keys(props.sortLabels) as SortKey[]"
                    :key="key"
                    role="option"
                    :aria-selected="props.sortKey === key"
                    @click="setKey(key)"
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
</template>
