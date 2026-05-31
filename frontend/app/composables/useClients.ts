import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { useWorkspace } from './useWorkspace'
import { encryptField, decryptField } from '../utils/crypto'
import type { Client } from '../types/domain'

const clients = ref<Client[]>([])
const loading = ref(false)

export function useClients() {
  const { currentWorkspace, activeCryptoKey } = useWorkspace()

  // Reactively refresh client list when database changes on the Rust side
  listen('db_changed', (event) => {
    if (event.payload === 'client') {
      console.log("Database changed event received for client, reloading...")
      fetchClients()
    }
  })

  async function fetchClients() {
    if (!currentWorkspace.value) return
    loading.value = true
    try {
      const result = await invoke<Client[]>('get_clients', { workspaceId: currentWorkspace.value.id })
      
      // Decrypt sensitive fields locally in browser memory
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
      // Encrypt sensitive fields before sending over local secure IPC
      const encryptedName = await encryptField(name, activeCryptoKey.value)
      const encryptedInfo = info ? await encryptField(info, activeCryptoKey.value) : null
      
      const newId = await invoke<string>('create_client', {
        workspaceId: currentWorkspace.value.id,
        name: encryptedName,
        info: encryptedInfo
      })

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
      await invoke('delete_client', { id, workspaceId: currentWorkspace.value.id })
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
