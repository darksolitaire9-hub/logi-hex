<script setup lang="ts">
const props = defineProps<{
    selected: boolean;
    title: string;
    description: string;
}>();

const emit = defineEmits<{
    (e: "select"): void;
}>();

const handleClick = () => emit("select");
</script>

<template>
    <div
        class="flex items-start gap-3 rounded-lg border p-3 sm:p-4 cursor-pointer transition-colors"
        :class="
            selected
                ? 'border-primary-500 bg-primary-500/10'
                : 'border-gray-700 hover:border-gray-500'
        "
        @click="handleClick"
    >
        <div
            class="mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 transition-colors"
            :class="selected ? 'border-primary-500' : 'border-gray-500'"
        >
            <div v-if="selected" class="h-2 w-2 rounded-full bg-primary-500" />
        </div>

        <div class="flex-1">
            <p class="text-sm font-medium text-gray-50">
                {{ title }}
            </p>
            <p class="text-xs text-gray-400 mt-0.5">
                {{ description }}
            </p>
        </div>
    </div>
</template>
