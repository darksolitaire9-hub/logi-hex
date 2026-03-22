// frontend/app/composables/useWorkspace.ts

import { ref } from "vue";
import type { Workspace, WorkspaceContext } from "../../lib/api/types";
import { listWorkspaces } from "../../lib/api/workspaces";

// shared state (singleton across the app)
const workspaces = ref<Workspace[]>([]);
const currentWorkspace = ref<WorkspaceContext | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);

export function useWorkspace() {
  async function loadWorkspaces(): Promise<void> {
    isLoading.value = true;
    error.value = null;
    try {
      workspaces.value = await listWorkspaces();
    } catch (_err) {
      error.value = "Failed to load workspaces.";
    } finally {
      isLoading.value = false;
    }
  }

  function selectWorkspace(workspace: Workspace): void {
    currentWorkspace.value = {
      id: workspace.id,
      mode: workspace.mode,
    };
  }

  return {
    workspaces,
    currentWorkspace,
    isLoading,
    error,
    loadWorkspaces,
    selectWorkspace,
  };
}
