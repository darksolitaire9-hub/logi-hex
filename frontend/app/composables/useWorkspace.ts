import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import type { Workspace } from '../types/domain'
import { deriveKeyFromPin } from '../utils/crypto'

async function hashPin(pin: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(pin)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

const workspaces = ref<Workspace[]>([])
const currentWorkspace = ref<Workspace | null>(null)
const activeCryptoKey = ref<CryptoKey | null>(null)

export function useWorkspace() {
  const loading = ref(false)

  async function fetchWorkspaces() {
    loading.value = true
    try {
      const db = await useDatabase()
      const result = await db.select<Workspace[]>('SELECT * FROM workspaces ORDER BY created_at DESC')
      workspaces.value = result
    } catch (e) {
      console.error('Failed to fetch workspaces:', e)
    } finally {
      loading.value = false
    }
  }

  async function createWorkspace(name: string, mode: 'ACCOUNTS' | 'INVENTORY', pin: string, adminPin: string, timezone: string = 'UTC') {
    loading.value = true
    try {
      const db = await useDatabase()
      const newId = uuidv4()
      
      const pinHash = await hashPin(pin)
      const adminPinHash = await hashPin(adminPin)

      await db.execute(
        'INSERT INTO workspaces (id, name, mode, pin_hash, admin_pin_hash, timezone) VALUES ($1, $2, $3, $4, $5, $6)',
        [newId, name, mode, pinHash, adminPinHash, timezone]
      )

      await fetchWorkspaces()
      
      const created = workspaces.value.find(w => w.id === newId)
      if (created) {
        currentWorkspace.value = created
      }
      return created
    } catch (e) {
      console.error('Failed to create workspace:', e)
      return null
    } finally {
      loading.value = false
    }
  }

  async function verifyPin(workspace: Workspace, pinToVerify: string): Promise<boolean> {
    const hashed = await hashPin(pinToVerify)
    return hashed === workspace.pin_hash
  }

  async function verifyAdminPin(workspace: Workspace, pinToVerify: string): Promise<boolean> {
    const hashed = await hashPin(pinToVerify)
    return hashed === workspace.admin_pin_hash
  }

  async function unlockWorkspaceCrypto(pin: string) {
    if (!currentWorkspace.value) return
    try {
      activeCryptoKey.value = await deriveKeyFromPin(pin, currentWorkspace.value.id)
    } catch (e) {
      console.error('Failed to derive crypto key', e)
    }
  }

  async function selectWorkspace(id: string) {
    const found = workspaces.value.find(w => w.id === id)
    if (found) {
      currentWorkspace.value = found
      // Save selection to local storage for persistence across reloads
      localStorage.setItem('lh_active_workspace', id)
    }
  }

  async function restoreActiveWorkspace() {
    if (workspaces.value.length === 0) {
      await fetchWorkspaces()
    }
    const savedId = localStorage.getItem('lh_active_workspace')
    if (savedId) {
      selectWorkspace(savedId)
    }
  }

  return {
    workspaces,
    currentWorkspace,
    activeCryptoKey,
    loading,
    fetchWorkspaces,
    createWorkspace,
    selectWorkspace,
    restoreActiveWorkspace,
    verifyPin,
    verifyAdminPin,
    unlockWorkspaceCrypto
  }
}
