// frontend/app/types/domain.ts

export type WorkspaceMode = 'ACCOUNTS' | 'INVENTORY'

export interface Workspace {
  id: string
  name: string
  mode: WorkspaceMode
  password_hash: string | null
  created_at: string
}

export interface Client {
  id: string
  workspace_id: string
  name: string
  created_at: string
}

export interface Item {
  id: string
  workspace_id: string
  label: string
  unit: string
  current_stock: number
  reorder_point: number | null
  created_at: string
}

export type MovementDirection = 'SEND' | 'COLLECT' | 'RECEIVE' | 'USE' | 'CORRECT'
export type CorrectionReason = 'DAMAGE' | 'LOSS' | 'COUNT_ADJUSTMENT' | 'OTHER'

export interface Movement {
  id: string
  workspace_id: string
  direction: MovementDirection
  timestamp: string
  client_id: string | null
  correction_reason: CorrectionReason | null
  notes: string | null
}

export interface MovementLineItem {
  id: string
  movement_id: string
  item_id: string
  quantity: number
}

// Helper types for the UI forms
export interface CreateWorkspacePayload {
  name: string
  mode: WorkspaceMode
  password_hash: string | null
}

export interface LogMovementPayload {
  direction: MovementDirection
  client_id?: string
  correction_reason?: CorrectionReason
  notes?: string
  lines: Array<{
    item_id: string
    quantity: number
  }>
}
