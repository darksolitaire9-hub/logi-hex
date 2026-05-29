<script setup lang="ts">
import type { PropType } from "vue";
import WorkspaceCard from "@/components/workspaces/WorkspaceCard.vue";

type WorkspaceMode = "ACCOUNTS" | "INVENTORY";

interface Workspace {
    id: string;
    name: string;
    mode: WorkspaceMode;
    createdAt: string | Date;
}

const props = defineProps({
    workspaces: {
        type: Array as PropType<Workspace[]>,
        required: true,
    },
    loadingId: {
        type: String as PropType<string | null>,
        default: null,
    },
});

const emit = defineEmits<{
    (e: "select", id: string): void;
}>();

const handleSelect = (id: string) => {
    emit("select", id);
};
</script>

<template>
    <div class="grid gap-3 md:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        <WorkspaceCard
            v-for="w in workspaces"
            :key="w.id"
            :workspace="{
                ...w,
                loading: loadingId === w.id,
            }"
            @select="handleSelect"
        />
    </div>
</template>
