import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
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
  const { currentWorkspace } = useWorkspace()

  async function logMovement(payload: LogMovementPayload) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    if (payload.lines.length === 0) throw new Error('Cannot log empty movement')
    
    loading.value = true
    try {
      const db = await useDatabase()
      const movementId = uuidv4()
      
      // Execute atomically. Tauri Plugin SQL doesn't expose a BEGIN/COMMIT API directly in JS 
      // for bulk inserts easily without raw string manipulation, but we can execute sequentially.
      // Better yet, we can run a single batch string or standard sequential await since SQLite is fast.
      
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
            payload.notes || null
          ]
        )

        for (const line of payload.lines) {
          if (line.quantity <= 0) continue;
          await db.execute(
            `INSERT INTO movement_line_items (id, movement_id, item_id, quantity) 
             VALUES ($1, $2, $3, $4)`,
            [uuidv4(), movementId, line.item_id, line.quantity]
          )
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
      return await db.select<MovementHistoryRow[]>(query, [currentWorkspace.value.id, clientId])
    } catch (e) {
      console.error('Failed to fetch client history:', e)
      return []
    }
  }

  return {
    loading,
    logMovement,
    fetchClientHistory
  }
}
