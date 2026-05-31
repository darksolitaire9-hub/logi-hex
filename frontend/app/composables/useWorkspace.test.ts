import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWorkspace } from './useWorkspace'

import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'

// Mock Tauri APIs
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}))

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn(() => Promise.resolve(() => {})),
}))

// Mock crypto module
vi.mock('../utils/crypto', () => ({
  deriveKeyFromPin: vi.fn(() => Promise.resolve({} as CryptoKey)),
}))

describe('useWorkspace Composable', () => {
  const { workspaces, currentWorkspace, activeCryptoKey, loading } = useWorkspace()

  beforeEach(() => {
    vi.clearAllMocks()
    workspaces.value = []
    currentWorkspace.value = null
    activeCryptoKey.value = null
    loading.value = false
    localStorage.clear()
  })

  it('fetchWorkspaces should fetch workspaces and update state', async () => {
    const mockData = [
      { id: '1', name: 'Inventory Workspace', mode: 'INVENTORY', timezone: 'UTC' }
    ]
    vi.mocked(invoke).mockResolvedValueOnce(mockData)

    const { fetchWorkspaces } = useWorkspace()
    await fetchWorkspaces()

    expect(invoke).toHaveBeenCalledWith('get_workspaces')
    expect(workspaces.value).toEqual(mockData)
  })

  it('createWorkspace should call invoke and update workspaces', async () => {
    const mockCreated = { id: '2', name: 'New Workspace', mode: 'ACCOUNTS', timezone: 'UTC' }
    vi.mocked(invoke)
      .mockResolvedValueOnce(mockCreated) // First call: create_workspace
      .mockResolvedValueOnce([mockCreated]) // Second call: fetchWorkspaces (get_workspaces)

    const { createWorkspace } = useWorkspace()
    const result = await createWorkspace('New Workspace', 'ACCOUNTS', '1234', '5678', 'UTC')

    expect(invoke).toHaveBeenNthCalledWith(1, 'create_workspace', {
      name: 'New Workspace',
      mode: 'ACCOUNTS',
      pin: '1234',
      adminPin: '5678',
      timezone: 'UTC'
    })
    expect(result).toEqual(mockCreated)
    expect(currentWorkspace.value).toEqual(mockCreated)
    expect(workspaces.value).toEqual([mockCreated])
  })

  it('selectWorkspace should set currentWorkspace and save to localStorage', async () => {
    const mockWorkspaces = [
      { id: 'ws-1', name: 'WS 1', mode: 'INVENTORY' },
      { id: 'ws-2', name: 'WS 2', mode: 'ACCOUNTS' }
    ]
    workspaces.value = mockWorkspaces

    const { selectWorkspace } = useWorkspace()
    await selectWorkspace('ws-2')

    expect(currentWorkspace.value).toEqual(mockWorkspaces[1])
    expect(localStorage.getItem('lh_active_workspace')).toBe('ws-2')
  })

  it('restoreActiveWorkspace should fetch workspaces and restore selection', async () => {
    const mockWorkspaces = [
      { id: 'ws-1', name: 'WS 1', mode: 'INVENTORY' }
    ]
    vi.mocked(invoke).mockResolvedValueOnce(mockWorkspaces)
    localStorage.setItem('lh_active_workspace', 'ws-1')

    const { restoreActiveWorkspace } = useWorkspace()
    await restoreActiveWorkspace()

    expect(invoke).toHaveBeenCalledWith('get_workspaces')
    expect(currentWorkspace.value).toEqual(mockWorkspaces[0])
  })
})
