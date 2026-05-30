import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { invoke } from '@tauri-apps/api/core'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import { encryptField, decryptField } from '../utils/crypto'
import type { MovementDirection } from '../types/generated/MovementDirection'
import type { CorrectionReason } from '../types/generated/CorrectionReason'
import type { MovementHistoryRow } from '../types/generated/MovementHistoryRow'
import { interpolateCensoredDemand } from '../utils/forecasting'
import { useUOMTranslator } from './useUOMTranslator'

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
  const { currentWorkspace, activeCryptoKey } = useWorkspace()
  const { translateToBase } = useUOMTranslator()

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
      const db = await useDatabase()
      
      // Query item's current stock for backward replay
      const itemRes = await db.select<{current_stock: number}[]>(
        'SELECT current_stock FROM items WHERE id = $1 AND workspace_id = $2', 
        [itemId, currentWorkspace.value.id]
      )
      if (itemRes.length === 0) return []
      let currentStock = itemRes[0].current_stock

      // Query daily demand AND daily net inventory change
      const rows = await db.select<{ date: string, demand_qty: number, net_change: number }[]>(
        `SELECT 
           m.local_date as date,
           SUM(CASE WHEN m.direction IN ('SEND', 'USE') THEN mli.quantity ELSE 0 END) as demand_qty,
           SUM(CASE 
                 WHEN m.direction IN ('RECEIVE', 'CORRECT', 'COLLECT') THEN mli.quantity 
                 WHEN m.direction IN ('SEND', 'USE') THEN -mli.quantity
                 ELSE 0 
               END) as net_change
         FROM movement_line_items mli
         JOIN movements m ON mli.movement_id = m.id
         WHERE mli.item_id = $1
           AND m.workspace_id = $2
         GROUP BY m.local_date
         ORDER BY m.local_date ASC`,
        [itemId, currentWorkspace.value.id]
      )

      if (rows.length === 0) return []

      const firstDateStr = rows[0].date
      const firstDate = new Date(firstDateStr + 'T00:00:00Z')
      const tz = currentWorkspace.value.timezone || 'UTC'
      const todayStr = new Intl.DateTimeFormat('en-CA', { timeZone: tz }).format(new Date())
      const endDate = new Date(todayStr + 'T00:00:00Z')
      
      const demandByDate = new Map<string, number>()
      const netChangeByDate = new Map<string, number>()
      for (const row of rows) {
        demandByDate.set(row.date, row.demand_qty)
        netChangeByDate.set(row.date, row.net_change)
      }

      // Generate continuous dates
      const dates: string[] = []
      let currentDate = new Date(firstDate)
      while (currentDate <= endDate) {
        dates.push(currentDate.toISOString().split('T')[0])
        currentDate.setUTCDate(currentDate.getUTCDate() + 1)
      }

      // Reconstruct historical stock balances (Backwards Replay)
      const stockByDate = new Map<string, number>()
      let runningStock = currentStock
      for (let i = dates.length - 1; i >= 0; i--) {
        const dateStr = dates[i]
        stockByDate.set(dateStr, runningStock)
        const netChange = netChangeByDate.get(dateStr) || 0
        runningStock -= netChange // Step back in time
      }

      // Identify Censored Demand (0 stock and 0 usage)
      const rawDemand: (number | null)[] = []
      for (let i = 0; i < dates.length; i++) {
        const dateStr = dates[i]
        const stock = stockByDate.get(dateStr)!
        const demand = demandByDate.get(dateStr) || 0
        
        if (stock <= 0 && demand === 0) {
          rawDemand.push(null) // Mask for interpolation
        } else {
          rawDemand.push(demand)
        }
      }

      // Perform Linear Interpolation using pure utility
      return interpolateCensoredDemand(rawDemand)
    } catch (e) {
      console.error('Failed to fetch item movement history:', e)
      return []
    }
  }

  async function saveForecastAudit(payload: {
    item_id: string,
    model_used: string,
    input_snapshot: string,
    base_prediction: number,
    human_override_percentage: number,
    human_adjustment_qty: number,
    override_reason: string,
    final_prediction: number
  }) {
    if (!currentWorkspace.value) return
    try {
      await invoke('save_forecast_audit', { payload })
    } catch (e) {
      console.error('Failed to save forecast audit:', e)
    }
  }

  return {
    loading,
    logMovement,
    fetchClientHistory,
    fetchGlobalHistory,
    getItemMovementHistory,
    saveForecastAudit
  }
}
