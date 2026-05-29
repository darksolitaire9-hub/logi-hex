<!-- frontend/app/components/setup/WorkspacePicker.vue -->
<script setup lang="ts">
import { onMounted } from "vue";
import { useWorkspace } from "~/composables/useWorkspace";
import { WorkspaceMode, MODE_LABELS } from "/../lib/constants/language";

const {
  workspaces,
  currentWorkspace,
  isLoading,
  error,
  loadWorkspaces,
  selectWorkspace,
} = useWorkspace();

onMounted(() => {
  loadWorkspaces();
});

function handleSelect(id: string) {
  const ws = workspaces.value.find((w) => w.id === id);
  if (ws) selectWorkspace(ws);
}

const MODE_STYLES = {
  [WorkspaceMode.ACCOUNTS]: "bg-blue-50 text-blue-600",
  [WorkspaceMode.INVENTORY]: "bg-green-50 text-green-600",
  default: "bg-gray-100 text-gray-500",
};

function modeBadgeClasses(mode: WorkspaceMode) {
  return MODE_STYLES[mode] || MODE_STYLES.default;
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-10 bg-[#F9F9FB]">
    <div class="w-full max-w-lg">
      <!-- Header -->
      <div class="mb-10 text-center">
        <div class="w-12 h-12 rounded-2xl bg-[#1A1A2E] flex items-center justify-center mx-auto mb-4">
          <span class="text-white text-sm font-bold tracking-tight">LH</span>
        </div>

        <h1 class="text-xl font-semibold text-[#1A1A2E] mb-1">
          Pick your workspace
        </h1>

        <p class="text-sm text-[#717182]">
          One workspace per operation. Choose where you’re working now.
        </p>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="space-y-3">
        <div class="h-14 bg-gray-200 animate-pulse rounded-xl"></div>
        <div class="h-14 bg-gray-200 animate-pulse rounded-xl"></div>
      </div>

      <!-- Error -->
      <p v-if="error" class="text-sm text-red-600 mb-4 text-center">
        {{ error }}
      </p>

      <!-- Workspace list -->
      <div v-if="!isLoading && workspaces.length" class="space-y-4">
        <button
          v-for="ws in workspaces"
          :key="ws.id"
          type="button"
          class="w-full text-left rounded-2xl border border-gray-200 bg-white px-6 py-5 flex items-center justify-between gap-4 transition-all hover:shadow-sm"
          :class="currentWorkspace?.id === ws.id ? 'border-[#1A1A2E] bg-gray-100' : ''"
          @click="handleSelect(ws.id)"
          :aria-selected="currentWorkspace?.id === ws.id"
        >
          <div class="flex flex-col min-w-0">
            <span class="text-base font-medium text-[#1A1A2E] truncate">
              {{ ws.name }}
            </span>
            <span class="text-xs text-[#717182]">Workspace</span>
          </div>

          <span
            class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium shrink-0"
            :class="modeBadgeClasses(ws.mode)"
          >
            {{ MODE_LABELS[ws.mode] }}
          </span>
        </button>
      </div>

      <!-- Empty state -->
      <div
        v-if="!isLoading && !workspaces.length && !error"
        class="mt-6 text-center text-sm text-[#717182] border border-dashed border-gray-300 rounded-2xl px-6 py-10 bg-white"
      >
        <div class="text-2xl mb-2">🗂️</div>
        No workspaces yet.
        <span class="block text-xs mt-1">
          You’ll see your workspaces here once they’re created.
        </span>
      </div>
    </div>
  </div>
</template>
