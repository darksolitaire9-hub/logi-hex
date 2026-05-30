import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import { encryptField, decryptField } from '../utils/crypto'
import type { Movement, MovementDirection, CorrectionReason } from '../types/domain'
import { interpolateCensoredDemand } from '../utils/forecasting'
import { useUOMTranslator } from './useUOMTranslator'

export interface LogMovementPayload {
  direction: MovementDirection
  client_id?: string
  correction_reason?: CorrectionReason
  notes?: string
  lines: Array<{
    item_id: string
    quantity: number
    recorded_unit?: string
    multiplier?: number
  }>
}

export interface MovementHistoryRow extends Movement {
  item_label: string
  quantity: number
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
      const db = await useDatabase()
      const movementId = uuidv4()
      
      const encryptedNotes = payload.notes ? await encryptField(payload.notes, activeCryptoKey.value) : null
      
      await db.execute('BEGIN TRANSACTION')
      
      try {
        const tz = currentWorkspace.value.timezone || 'UTC'
        const localDate = new Intl.DateTimeFormat('en-CA', { timeZone: tz }).format(new Date())

        await db.execute(
          `INSERT INTO movements (id, workspace_id, direction, client_id, correction_reason, notes, local_date) 
           VALUES ($1, $2, $3, $4, $5, $6, $7)`,
          [
            movementId, 
            currentWorkspace.value.id, 
            payload.direction, 
            payload.client_id || null, 
            payload.correction_reason || null, 
            encryptedNotes,
            localDate
          ]
        )

        for (const line of payload.lines) {
          const finalQuantity = translateToBase(line.quantity, line.multiplier || 1)
          if (finalQuantity <= 0) continue;

          // PRE-FLIGHT CHECK: Prevent Negative Inventory
          if (payload.direction === 'USE' || payload.direction === 'SEND') {
            const itemRes = await db.select<{current_stock: number}[]>(
              `SELECT current_stock FROM items WHERE id = $1 AND workspace_id = $2`,
              [line.item_id, currentWorkspace.value.id]
            )
            if (itemRes.length > 0) {
              const currentStock = itemRes[0].current_stock
              if (finalQuantity > currentStock) {
                throw new Error(`Insufficient stock for item. You cannot send/use ${finalQuantity} units when only ${currentStock} are available.`)
              }
            }
          }
          
          await db.execute(
            `INSERT INTO movement_line_items (id, movement_id, item_id, quantity, recorded_unit) 
             VALUES ($1, $2, $3, $4, $5)`,
            [uuidv4(), movementId, line.item_id, finalQuantity, line.recorded_unit || null]
          )

          if (payload.direction === 'RECEIVE' || payload.direction === 'CORRECT' || payload.direction === 'COLLECT') {
            await db.execute(
              `UPDATE items SET current_stock = current_stock + $1 WHERE id = $2 AND workspace_id = $3`,
              [finalQuantity, line.item_id, currentWorkspace.value.id]
            )
          } else if (payload.direction === 'USE' || payload.direction === 'SEND') {
            await db.execute(
              `UPDATE items SET current_stock = current_stock - $1 WHERE id = $2 AND workspace_id = $3`,
              [finalQuantity, line.item_id, currentWorkspace.value.id]
            )
          }
          
          if (payload.client_id && (payload.direction === 'SEND' || payload.direction === 'COLLECT')) {
            const balanceDelta = payload.direction === 'SEND' ? finalQuantity : -finalQuantity;
            await db.execute(
              `INSERT INTO client_item_balances (id, workspace_id, client_id, item_id, balance)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT(workspace_id, client_id, item_id) 
               DO UPDATE SET balance = balance + excluded.balance`,
              [uuidv4(), currentWorkspace.value.id, payload.client_id, line.item_id, balanceDelta]
            )
          }
        }
        
        await db.execute('COMMIT')
        return movementId
      } catch (err) {
        await db.execute('ROLLBACK')
        throw err
      }
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
      const db = await useDatabase()
      const query = `
        SELECT 
          m.*,
          mli.quantity,
          i.label as item_label
        FROM movements m
        JOIN movement_line_items mli ON m.id = mli.movement_id
        JOIN items i ON mli.item_id = i.id
        WHERE m.workspace_id = $1 AND m.client_id = $2
        ORDER BY m.timestamp DESC
      `
      const result = await db.select<MovementHistoryRow[]>(query, [currentWorkspace.value.id, clientId])
      
      // Decrypt sensitive fields
      for (const row of result) {
        row.item_label = await decryptField(row.item_label, activeCryptoKey.value)
        if (row.notes) {
          row.notes = await decryptField(row.notes, activeCryptoKey.value) || null
        }
      }
      
      return result
    } catch (e) {
      console.error('Failed to fetch client history:', e)
      return []
    }
  }

  async function fetchGlobalHistory(): Promise<MovementHistoryRow[]> {
    if (!currentWorkspace.value) return []
    try {
      const db = await useDatabase()
      const query = `
        SELECT 
          m.*,
          mli.quantity,
          i.label as item_label
        FROM movements m
        JOIN movement_line_items mli ON m.id = mli.movement_id
        JOIN items i ON mli.item_id = i.id
        WHERE m.workspace_id = $1
        ORDER BY m.timestamp DESC
      `
      const result = await db.select<MovementHistoryRow[]>(query, [currentWorkspace.value.id])
      
      // Decrypt sensitive fields
      for (const row of result) {
        row.item_label = await decryptField(row.item_label, activeCryptoKey.value)
        if (row.notes) {
          row.notes = await decryptField(row.notes, activeCryptoKey.value) || null
        }
      }
      
      return result
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
      const db = await useDatabase()
      await db.execute(
        `INSERT INTO forecast_audit_logs 
         (item_id, model_used, input_snapshot, base_prediction, human_override_percentage, human_adjustment_qty, override_reason, final_prediction)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [
          payload.item_id,
          payload.model_used,
          payload.input_snapshot,
          payload.base_prediction,
          payload.human_override_percentage,
          payload.human_adjustment_qty,
          payload.override_reason,
          payload.final_prediction
        ]
      )
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
