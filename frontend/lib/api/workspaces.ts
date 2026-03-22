// frontend/lib/api/workspaces.ts

import type { Workspace } from "./types";
import { useApiClient } from "../../app/composables/useApiClient";

/**
 * List workspaces available to the current user.
 * Adjust the path if your backend exposes a different route.
 */
export async function listWorkspaces(): Promise<Workspace[]> {
  return await useApiClient()("/api/workspaces");
}
