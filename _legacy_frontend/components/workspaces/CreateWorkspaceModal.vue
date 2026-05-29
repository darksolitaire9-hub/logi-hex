<script setup lang="ts">
import { ref, watch } from "vue";
import WorkspaceModeSelector from "@/components/workspaces/WorkspaceModeSelector.vue";

type WorkspaceMode = "ACCOUNTS" | "INVENTORY";

const isOpen = defineModel<boolean>("open", { default: false });

const props = defineProps<{
    loading?: boolean;
    error?: string | null;
}>();

const emit = defineEmits<{
    (e: "submit", payload: { name: string; mode: WorkspaceMode }): void;
}>();

const name = ref("");
const mode = ref<WorkspaceMode | null>(null);
const localError = ref<string | null>(null);

watch(isOpen, (val) => {
    if (val) {
        name.value = "";
        mode.value = null;
        localError.value = null;
    }
});

watch(
    () => props.error,
    (val) => {
        if (val) localError.value = val;
    },
);

const handleSubmit = () => {
    const trimmed = name.value.trim();
    if (!trimmed) {
        localError.value = "Please enter a workspace name";
        return;
    }
    if (!mode.value) {
        localError.value = "Please select a mode";
        return;
    }
    emit("submit", { name: trimmed, mode: mode.value });
};

const handleCancel = () => {
    isOpen.value = false;
};
</script>

<template>
    <UModal v-model:open="isOpen">
        <template #content>
            <div class="p-4 sm:p-6 space-y-4">
                <div>
                    <h2 class="text-base sm:text-lg font-semibold text-gray-50">
                        Create new workspace
                    </h2>
                    <p class="mt-1 text-xs sm:text-sm text-gray-400">
                        Set up a new workspace to track your items and
                        movements.
                    </p>
                </div>

                <div class="space-y-1">
                    <label
                        for="workspace-name"
                        class="block text-xs font-medium text-gray-200"
                    >
                        Workspace name
                    </label>
                    <UInput
                        id="workspace-name"
                        v-model="name"
                        placeholder="e.g., Main Warehouse"
                        @keydown.enter.prevent="handleSubmit"
                    />
                </div>

                <WorkspaceModeSelector v-model="mode" />

                <p v-if="localError" class="text-xs text-red-400">
                    {{ localError }}
                </p>

                <div class="flex flex-col sm:flex-row justify-end gap-2 pt-2">
                    <UButton
                        variant="ghost"
                        class="w-full sm:w-auto flex items-center justify-center text-center"
                        @click="handleCancel"
                    >
                        Cancel
                    </UButton>
                    <UButton
                        color="primary"
                        class="w-full sm:w-auto flex items-center justify-center text-center"
                        :loading="loading"
                        @click="handleSubmit"
                    >
                        Create workspace
                    </UButton>
                </div>
            </div>
        </template>
    </UModal>
</template>
