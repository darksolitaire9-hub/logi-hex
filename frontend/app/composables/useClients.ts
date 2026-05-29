import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import type { Client } from '../types/domain'

export interface ClientWithBalance extends Client {
  total_items_held?: number
}

export function useClients() {
  const clients = ref<ClientWithBalance[]>([])
  const loading = ref(false)
  const { currentWorkspace } = useWorkspace()

  async function fetchClients() {
    if (!currentWorkspace.value) return
    loading.value = true
    try {
      const db = await useDatabase()
      // We will grab clients and do a quick join/subquery to find out how many items they hold.
      // A SEND is positive for the client. A COLLECT is negative.
      // E.g., if we sent 50 pallets, and collected 20, they hold 30.
      const query = `
        SELECT 
          c.*,
          COALESCE((
            SELECT SUM(
              CASE 
                WHEN m.direction = 'SEND' THEN mli.quantity
                WHEN m.direction = 'COLLECT' THEN -mli.quantity
                ELSE 0 
              END
            )
            FROM movements m
            JOIN movement_line_items mli ON mli.movement_id = m.id
            WHERE m.client_id = c.id
          ), 0) as total_items_held
        FROM clients c
        WHERE c.workspace_id = $1
        ORDER BY c.name ASC
      `
      
      const result = await db.select<ClientWithBalance[]>(query, [currentWorkspace.value.id])
      clients.value = result
    } catch (e) {
      console.error('Failed to fetch clients:', e)
    } finally {
      loading.value = false
    }
  }

  async function createClient(name: string) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    try {
      const db = await useDatabase()
      const newId = uuidv4()
      await db.execute(
        'INSERT INTO clients (id, workspace_id, name) VALUES ($1, $2, $3)',
        [newId, currentWorkspace.value.id, name]
      )
      await fetchClients()
      return newId
    } catch (e) {
      console.error('Failed to create client:', e)
      throw e
    }
  }

  return {
    clients,
    loading,
    fetchClients,
    createClient
  }
}
