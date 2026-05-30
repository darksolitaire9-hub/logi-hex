import { ref } from 'vue'
import { useDatabase } from './useDatabase'
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
      const db = await useDatabase()
      // Enterprise Proactive Alerting:
      // We rely entirely on the individual 'reorder_point' set by the user.
      const query = `
        SELECT * FROM items 
        WHERE workspace_id = $1 
          AND deleted_at IS NULL 
          AND reorder_point IS NOT NULL 
          AND current_stock <= reorder_point
        ORDER BY current_stock ASC
      `
      const result = await db.select<Item[]>(query, [currentWorkspace.value.id])
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
