<script setup lang="ts">
import { Package, Plus } from "lucide-vue-next";

const emit = defineEmits<{
    (e: "open-create"): void;
}>();

const handleClick = () => emit("open-create");
</script>

<template>
    <UCard
        class="border border-dashed border-gray-700 bg-gray-900/60 text-gray-100"
    >
        <div
            class="flex flex-col items-center justify-center py-10 md:py-12 px-4"
        >
            <div
                class="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-gray-800"
            >
                <Package class="h-6 w-6 text-gray-400" />
            </div>
            <p class="mb-4 text-center text-sm text-gray-400">
                You don’t have any workspaces yet.
            </p>
            <UButton
                color="primary"
                class="w-full sm:w-auto flex items-center justify-center gap-2"
                @click="handleClick"
            >
                <Plus class="h-4 w-4" />
                <span>Create your first workspace</span>
            </UButton>
        </div>
    </UCard>
</template>
