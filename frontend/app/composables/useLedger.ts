import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import { encryptField, decryptField } from '../utils/crypto'
import type { Movement, MovementDirection, CorrectionReason } from '../types/domain'

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

export interface MovementHistoryRow extends Movement {
  item_label: string
  quantity: number
}

export function useLedger() {
  const loading = ref(false)
  const { currentWorkspace, activeCryptoKey } = useWorkspace()

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
        await db.execute(
          `INSERT INTO movements (id, workspace_id, direction, client_id, correction_reason, notes) 
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [
            movementId, 
            currentWorkspace.value.id, 
            payload.direction, 
            payload.client_id || null, 
            payload.correction_reason || null, 
            encryptedNotes
          ]
        )

        for (const line of payload.lines) {
          if (line.quantity <= 0) continue;
          
          await db.execute(
            `INSERT INTO movement_line_items (id, movement_id, item_id, quantity) 
             VALUES ($1, $2, $3, $4)`,
            [uuidv4(), movementId, line.item_id, line.quantity]
          )

          if (payload.direction === 'RECEIVE' || payload.direction === 'CORRECT') {
            await db.execute(
              `UPDATE items SET current_stock = current_stock + $1 WHERE id = $2 AND workspace_id = $3`,
              [line.quantity, line.item_id, currentWorkspace.value.id]
            )
          } else if (payload.direction === 'USE') {
            await db.execute(
              `UPDATE items SET current_stock = current_stock - $1 WHERE id = $2 AND workspace_id = $3`,
              [line.quantity, line.item_id, currentWorkspace.value.id]
            )
          }
          
          if (payload.client_id && (payload.direction === 'SEND' || payload.direction === 'COLLECT')) {
            const balanceDelta = payload.direction === 'SEND' ? line.quantity : -line.quantity;
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
      const rows = await db.select<{ qty: number }[]>(
        `SELECT 
           SUM(CASE WHEN m.direction IN ('SEND', 'USE') THEN -mli.quantity ELSE mli.quantity END) as qty
         FROM movement_line_items mli
         JOIN movements m ON mli.movement_id = m.id
         WHERE mli.item_id = $1
           AND m.workspace_id = $2
         GROUP BY date(m.timestamp)
         ORDER BY date(m.timestamp) ASC`,
        [itemId, currentWorkspace.value.id]
      )
      return rows.map(r => r.qty)
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
