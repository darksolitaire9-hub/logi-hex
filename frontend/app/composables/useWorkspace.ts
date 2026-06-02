import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
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

// Reactively refresh workspaces list when database changes on the Rust side
listen('db_changed', (event) => {
  if (event.payload === 'workspace') {
    console.log("Database changed event received for workspace, reloading...")
    fetchWorkspaces()
  }
})

async function fetchWorkspaces() {
  loading.value = true
  try {
    const result = await invoke<Workspace[]>('get_workspaces')
    workspaces.value = result
  } catch (e) {
    console.error('Failed to fetch workspaces:', e)
  } finally {
    loading.value = false
  }
}

const loading = ref(false)

export function useWorkspace() {
  async function createWorkspace(name: string, mode: 'ACCOUNTS' | 'INVENTORY', pin: string, adminPin: string, timezone: string = 'UTC') {
    loading.value = true
    try {
      const created = await invoke<Workspace>('create_workspace', {
        name,
        mode,
        pin,
        adminPin,
        timezone
      })

      await fetchWorkspaces()
      
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

  async function updateWorkspaceMode(mode: 'ACCOUNTS' | 'INVENTORY') {
    if (!currentWorkspace.value) return
    try {
      await invoke('update_workspace_mode', {
        id: currentWorkspace.value.id,
        mode
      })
      // Update local state
      currentWorkspace.value.mode = mode
    } catch (e) {
      console.error('Failed to update workspace mode:', e)
      throw e
    }
  }

  return {
    workspaces,
    currentWorkspace,
    activeCryptoKey,
    loading,
    fetchWorkspaces,
    createWorkspace,
    updateWorkspaceMode,
    selectWorkspace,
    restoreActiveWorkspace,
    verifyPin,
    verifyAdminPin,
    unlockWorkspaceCrypto
  }
}
