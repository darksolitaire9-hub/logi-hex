<script setup lang="ts">
import RadioCard from "@/components/common/RadioCard.vue";

type WorkspaceMode = "ACCOUNTS" | "INVENTORY";

const props = defineProps<{
    modelValue: WorkspaceMode | null;
}>();

const emit = defineEmits<{
    (e: "update:modelValue", value: WorkspaceMode | null): void;
}>();

const options = [
    {
        value: "ACCOUNTS" as WorkspaceMode,
        label: "Accounts",
        description:
            "Track items sent to and collected from clients. Best for equipment loans, rentals, or consignments.",
    },
    {
        value: "INVENTORY" as WorkspaceMode,
        label: "Inventory",
        description:
            "Track stock levels with receive, use, and correction operations. Best for warehouses or supply rooms.",
    },
];

const select = (value: WorkspaceMode) => {
    emit("update:modelValue", value);
};
</script>

<template>
    <div class="space-y-2">
        <p class="text-xs font-medium text-gray-200">Mode</p>

        <div class="space-y-2">
            <RadioCard
                v-for="option in options"
                :key="option.value"
                :selected="modelValue === option.value"
                :title="option.label"
                :description="option.description"
                @select="select(option.value)"
            />
        </div>

        <p class="text-[11px] text-gray-400">Mode cannot be changed later.</p>
    </div>
</template>
