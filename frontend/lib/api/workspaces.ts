// frontend/lib/api/workspaces.ts
// Workspace API port (stubbed for now, real backend later)

import type { Workspace } from "./types";
import { WorkspaceMode } from "../constants/language";

// STUB ONLY — replace with real API call when backend/auth is wired.
const stubWorkspaces: Workspace[] = [
  { id: "ws-1", name: "tx", mode: WorkspaceMode.ACCOUNTS },
  { id: "ws-2", name: "ix", mode: WorkspaceMode.INVENTORY },
];

export async function listWorkspaces(): Promise<Workspace[]> {
  return stubWorkspaces;
}
