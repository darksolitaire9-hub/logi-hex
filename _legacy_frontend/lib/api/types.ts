// frontend/lib/api/types.ts
// DDD-aligned API types (V1, workspaces-first)

import type { WorkspaceMode } from "../constants/language";

// Backend workspace entity (new API, workspaces-aware)
export interface Workspace {
  id: string;
  name: string;
  mode: WorkspaceMode;
}

// What the frontend stores as the currently selected workspace
export interface WorkspaceContext {
  id: string;
  mode: WorkspaceMode;
}
