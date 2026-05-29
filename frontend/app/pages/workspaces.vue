<script setup lang="ts">
import { ref, computed } from "vue";
import WorkspacesHeader from "@/components/workspaces/WorkspacesHeader.vue";
import WorkspacesEmptyState from "@/components/workspaces/WorkspacesEmptyState.vue";
import WorkspaceGrid from "@/components/workspaces/WorkspaceGrid.vue";
import CreateWorkspaceModal from "@/components/workspaces/CreateWorkspaceModal.vue";

type WorkspaceMode = "ACCOUNTS" | "INVENTORY";

interface Workspace {
    id: string;
    name: string;
    mode: WorkspaceMode;
    createdAt: string;
}

// TEMP mock user
const user = ref<{ name: string; email: string } | null>({
    name: "Demo User",
    email: "demo@example.com",
});

// TEMP mock workspaces list (start empty)
const workspaces = ref<Workspace[]>([]);

const isCreateOpen = ref(false);
const isCreating = ref(false);
const createError = ref<string | null>(null);
const selectingId = ref<string | null>(null);

const hasWorkspaces = computed(() => workspaces.value.length > 0);

const handleSubmitCreate = async (payload: {
    name: string;
    mode: WorkspaceMode;
}) => {
    createError.value = null;
    isCreating.value = true;
    try {
        // MOCK create
        workspaces.value.push({
            id: String(Date.now()),
            name: payload.name,
            mode: payload.mode,
            createdAt: new Date().toISOString(),
        });
        isCreateOpen.value = false;
    } catch (e) {
        createError.value = "Could not create workspace. Please try again.";
    } finally {
        isCreating.value = false;
    }
};

const handleSelectWorkspace = (id: string) => {
    if (selectingId.value) return;
    selectingId.value = id;
    console.log("Selected workspace", id);
    setTimeout(() => {
        selectingId.value = null;
    }, 400);
};
</script>

<template>
    <div class="flex min-h-screen flex-col bg-gray-950 text-gray-50">
        <WorkspacesHeader :user="user" />

        <main
            class="flex flex-1 flex-col items-center px-3 md:px-4 lg:px-6 py-6 md:py-10"
        >
            <div class="w-full max-w-xl md:max-w-3xl">
                <div class="mb-6 md:mb-8 text-center">
                    <h1
                        class="text-xl md:text-2xl font-semibold tracking-tight"
                    >
                        Choose a workspace
                    </h1>
                    <p class="mt-2 text-xs md:text-sm text-gray-400">
                        Select an existing workspace or create a new one to get
                        started.
                    </p>
                </div>

                <!-- Empty state -->
                <div v-if="!hasWorkspaces" class="flex justify-center">
                    <div class="w-full max-w-md">
                        <WorkspacesEmptyState
                            @open-create="isCreateOpen = true"
                        />
                    </div>
                </div>

                <!-- Has workspaces -->
                <div v-else class="space-y-4">
                    <div class="flex justify-end mb-4 md:mb-6">
                        <button
                            class="inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium bg-primary-500 text-black hover:bg-primary-400 h-9 px-4 py-2"
                            @click="isCreateOpen = true"
                        >
                            <span class="text-base leading-none">+</span>
                            <span>Create new workspace</span>
                        </button>
                    </div>
                    <WorkspaceGrid
                        :workspaces="workspaces"
                        :loading-id="selectingId"
                        @select="handleSelectWorkspace"
                    />
                </div>

                <CreateWorkspaceModal
                    v-model:open="isCreateOpen"
                    :loading="isCreating"
                    :error="createError"
                    @submit="handleSubmitCreate"
                />
            </div>
        </main>
    </div>
</template>
