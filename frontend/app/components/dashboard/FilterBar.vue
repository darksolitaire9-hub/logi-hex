<script setup lang="ts">
import { computed, ref } from "vue";
import { Search, X } from "lucide-vue-next";

const props = defineProps<{
    modelValue: string;
    placeholder: string;
    disabled?: boolean;
}>();

const emit = defineEmits<{
    (e: "update:modelValue", value: string): void;
}>();

const inputRef = ref<HTMLInputElement | null>(null);
const hasValue = computed(() => props.modelValue.trim().length > 0);

function clear() {
    emit("update:modelValue", "");
    inputRef.value?.focus();
}

defineExpose({ focus: () => inputRef.value?.focus() });

</script>

<template>
    <div class="relative">
        <Search
            class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#a0a0b0] pointer-events-none"
            aria-hidden="true"
        />
        <input
            ref="inputRef"
            type="search"
            :disabled="props.disabled"
            :value="props.modelValue"
            @input="
                emit(
                    'update:modelValue',
                    ($event.target as HTMLInputElement).value,
                )
            "
            :placeholder="props.placeholder"
            aria-label="Filter"
            class="w-full pl-8 pr-8 py-2 rounded-lg border border-[rgba(0,0,0,0.1)] bg-white text-sm text-[#1a1a2e] placeholder:text-[#a0a0b0] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1a1a2e] transition-colors hover:border-[rgba(0,0,0,0.18)] disabled:opacity-60"
        />
        <button
            v-if="hasValue"
            type="button"
            @click="clear"
            aria-label="Clear filter"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#a0a0b0] hover:text-[#1a1a2e] transition-colors"
        >
            <X class="w-3.5 h-3.5" />
        </button>
    </div>
</template>
