import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useWorkspace } from './useWorkspace'
import type { MovementDirection } from '../types/generated/MovementDirection'
import type { CorrectionReason } from '../types/generated/CorrectionReason'
import type { MovementHistoryRow } from '../types/generated/MovementHistoryRow'

export interface LogMovementPayload {
  direction: MovementDirection
  client_id?: string
  correction_reason?: CorrectionReason | null
  notes?: string
  lines: Array<{
    item_id: string
    quantity: number
    recorded_unit?: string
    multiplier?: number
  }>
}

export function useLedger() {
  const loading = ref(false)
  const { currentWorkspace } = useWorkspace()

  async function logMovement(payload: LogMovementPayload) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    if (payload.lines.length === 0) throw new Error('Cannot log empty movement')
    
    loading.value = true
    try {
      const rustPayload = {
        ...payload,
        workspace_id: currentWorkspace.value.id,
        timezone: currentWorkspace.value.timezone || 'UTC'
      }
      
      const movementId = await invoke<string>('log_movement', { payload: rustPayload })
      return movementId
    } catch (e) {
      console.error('Failed to log movement:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchClientHistory(clientId: string): Promise<MovementHistoryRow[]> {
    if (!currentWorkspace.value) return []
    try {
      return await invoke<MovementHistoryRow[]>('fetch_client_history', { 
        workspaceId: currentWorkspace.value.id, 
        clientId 
      })
    } catch (e) {
      console.error('Failed to fetch client history:', e)
      return []
    }
  }

  async function fetchGlobalHistory(): Promise<MovementHistoryRow[]> {
    if (!currentWorkspace.value) return []
    try {
      return await invoke<MovementHistoryRow[]>('fetch_global_history', { 
        workspaceId: currentWorkspace.value.id 
      })
    } catch (e) {
      console.error('Failed to fetch global history:', e)
      return []
    }
  }

  async function getItemMovementHistory(itemId: string): Promise<number[]> {
    if (!currentWorkspace.value) return []
    try {
      return await invoke<number[]>('get_item_movement_history', { itemId })
    } catch (e) {
      console.error('Failed to fetch item movement history:', e)
      return []
    }
  }

  return {
    loading,
    logMovement,
    fetchClientHistory,
    fetchGlobalHistory,
    getItemMovementHistory
  }
}
