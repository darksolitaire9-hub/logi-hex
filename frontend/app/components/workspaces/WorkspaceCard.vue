<script setup lang="ts">
import type { PropType } from "vue";
import { Users, Package } from "lucide-vue-next";

type WorkspaceMode = "ACCOUNTS" | "INVENTORY";

interface WorkspaceCardProps {
    id: string;
    name: string;
    mode: WorkspaceMode;
    createdAt: string | Date;
    loading?: boolean;
}

const props = defineProps({
    workspace: {
        type: Object as PropType<WorkspaceCardProps>,
        required: true,
    },
});

const emit = defineEmits<{
    (e: "select", id: string): void;
}>();

const formatDate = (iso: string | Date) => {
    const d = typeof iso === "string" ? new Date(iso) : iso;
    return d.toLocaleDateString();
};

const handleClick = () => {
    if (props.workspace.loading) return;
    emit("select", props.workspace.id);
};
</script>

<template>
    <UCard
        class="cursor-pointer border border-gray-800 bg-gray-900/60 hover:bg-gray-900 transition-colors"
        @click="handleClick"
    >
        <template #header>
            <div class="flex items-start justify-between">
                <div
                    class="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-800"
                >
                    <Users
                        v-if="workspace.mode === 'ACCOUNTS'"
                        class="h-5 w-5 text-gray-400"
                    />
                    <Package v-else class="h-5 w-5 text-gray-400" />
                </div>
                <span
                    class="inline-flex items-center rounded-full bg-gray-800 px-2 py-0.5 text-[11px] uppercase tracking-wide text-gray-300"
                >
                    {{
                        workspace.mode === "ACCOUNTS" ? "Accounts" : "Inventory"
                    }}
                </span>
            </div>
        </template>

        <div class="flex flex-col gap-1">
            <div class="flex items-center justify-between gap-2">
                <p class="font-medium text-sm md:text-base truncate">
                    {{ workspace.name }}
                </p>
                <span
                    v-if="workspace.loading"
                    class="text-[11px] text-gray-400"
                >
                    Loading…
                </span>
            </div>
            <p class="text-xs md:text-sm text-gray-400">
                Created {{ formatDate(workspace.createdAt) }}
            </p>
        </div>
    </UCard>
</template>
