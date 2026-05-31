import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useWorkspace } from './useWorkspace'
import type { Item } from '../types/domain'

export function useAlerts() {
  const lowStockItems = ref<Item[]>([])
  const loading = ref(false)
  const { currentWorkspace } = useWorkspace()

  async function fetchAlerts() {
    if (!currentWorkspace.value || currentWorkspace.value.mode !== 'INVENTORY') return
    
    loading.value = true
    try {
      const result = await invoke<Item[]>('get_low_stock_items', {
        workspaceId: currentWorkspace.value.id
      })
      lowStockItems.value = result
    } catch (e) {
      console.error('Failed to fetch alerts:', e)
    } finally {
      loading.value = false
    }
  }

  return {
    lowStockItems,
    loading,
    fetchAlerts
  }
}
