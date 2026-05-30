// frontend/app/types/domain.ts

export type WorkspaceMode = 'ACCOUNTS' | 'INVENTORY'

export interface Workspace {
  id: string
  name: string
  pin_hash: string
  admin_pin_hash: string
  mode: 'ACCOUNTS' | 'INVENTORY'
  timezone?: string
  created_at: string
}

export interface Client {
  id: string
  workspace_id: string
  name: string
  info?: string
  created_at: string
  deleted_at?: string
}

export interface ItemUOM {
  id: string
  item_id: string
  unit_name: string
  multiplier: number
}

export interface Item {
  id: string
  workspace_id: string
  label: string
  unit: string
  base_unit_name: string
  primary_uom_id: string | null
  current_stock: number
  reorder_point: number | null
  created_at: string
  deleted_at?: string
  uoms?: ItemUOM[]
}
// Helper types for the UI forms
export interface CreateWorkspacePayload {
  name: string
  mode: WorkspaceMode
  password_hash: string | null
}

