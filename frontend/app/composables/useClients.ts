import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import { encryptField, decryptField } from '../utils/crypto'
import type { Client } from '../types/domain'

export function useClients() {
  const clients = ref<Client[]>([])
  const loading = ref(false)
  const { currentWorkspace, activeCryptoKey } = useWorkspace()

  async function fetchClients() {
    if (!currentWorkspace.value) return
    loading.value = true
    try {
      const db = await useDatabase()
      const query = `
        SELECT 
          c.*,
          COALESCE(SUM(b.balance), 0) as total_items_held
        FROM clients c
        LEFT JOIN client_item_balances b ON c.id = b.client_id
        WHERE c.workspace_id = $1
        GROUP BY c.id
        ORDER BY 
          CASE WHEN c.deleted_at IS NULL THEN 0 ELSE 1 END ASC,
          c.created_at DESC
      `
      const result = await db.select<Client[]>(query, [currentWorkspace.value.id])
      
      // Decrypt sensitive fields
      for (const client of result) {
        client.name = await decryptField(client.name, activeCryptoKey.value)
        if (client.info) {
          client.info = await decryptField(client.info, activeCryptoKey.value) || ''
        }
      }
      
      clients.value = result
    } catch (e) {
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function createClient(name: string, info: string) {
    if (!currentWorkspace.value) return null
    loading.value = true
    try {
      const db = await useDatabase()
      const newId = uuidv4()
      
      // Encrypt sensitive fields
      const encryptedName = await encryptField(name, activeCryptoKey.value)
      const encryptedInfo = info ? await encryptField(info, activeCryptoKey.value) : null
      
      await db.execute(
        'INSERT INTO clients (id, workspace_id, name, info) VALUES ($1, $2, $3, $4)',
        [newId, currentWorkspace.value.id, encryptedName, encryptedInfo]
      )
      await fetchClients()
      return newId
    } catch (e) {
      console.error(e)
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteClient(id: string) {
    if (!currentWorkspace.value) return
    try {
      const db = await useDatabase()
      await db.execute(
        'UPDATE clients SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND workspace_id = $2',
        [id, currentWorkspace.value.id]
      )
      await fetchClients()
    } catch (e) {
      console.error('Failed to delete client:', e)
    }
  }

  return {
    clients,
    loading,
    fetchClients,
    createClient,
    deleteClient
  }
}
