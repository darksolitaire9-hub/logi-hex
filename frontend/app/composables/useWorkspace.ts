import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import type { Workspace, CreateWorkspacePayload } from '../types/domain'

export function useWorkspace() {
  const workspaces = ref<Workspace[]>([])
  const currentWorkspace = ref<Workspace | null>(null)
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

  async function createWorkspace(payload: CreateWorkspacePayload) {
    try {
      const db = await useDatabase()
      const newId = uuidv4()
      await db.execute(
        'INSERT INTO workspaces (id, name, mode) VALUES ($1, $2, $3)',
        [newId, payload.name, payload.mode]
      )
      await fetchWorkspaces()
    } catch (e) {
      console.error('Failed to create workspace:', e)
      throw e
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
    loading,
    fetchWorkspaces,
    createWorkspace,
    selectWorkspace,
    restoreActiveWorkspace
  }
}
