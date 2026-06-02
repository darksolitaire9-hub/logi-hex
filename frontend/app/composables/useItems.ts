import { ref } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { useWorkspace } from './useWorkspace'
import type { Item, ItemUOM } from '../types/domain'

// Use ref for predictability in E2E
const items = ref<Item[]>([])
const loading = ref(false)

export function useItems() {
  const { currentWorkspace } = useWorkspace()

  // Accepts optional pagination and search parameters
  async function fetchItems(searchTerm?: string, cursor?: string, limit: number = 100) {
    if (!currentWorkspace.value) return
    
    loading.value = true
    try {
      const [itemRows, uomRows] = await invoke<[Item[], ItemUOM[]]>('get_items', { 
        workspaceId: currentWorkspace.value.id,
        searchTerm: searchTerm || null,
        cursor: cursor || null,
        limit
      })
      
      // Map UOMs
      for (const item of itemRows) {
        item.uoms = uomRows.filter(u => u.item_id === item.id)
      }
      
      // If we are paginating, append to the array. Otherwise, replace.
      if (cursor) {
        items.value = [...items.value, ...itemRows]
      } else {
        items.value = itemRows
      }
    } catch (e) {
      console.error('Failed to fetch items:', e)
    } finally {
      loading.value = false
    }
  }

  async function createItem(label: string, base_unit_name: string, reorder_point: number | null = null, alternate_uoms: Array<{unit_name: string, multiplier: number}> = [], primary_uom_name: string | null = null) {
    if (!currentWorkspace.value) return null
    try {
      const id = await invoke<string>('create_item', {
        workspaceId: currentWorkspace.value.id,
        label,
        baseUnitName: base_unit_name,
        reorderPoint: reorder_point,
        alternateUoms: alternate_uoms,
        primaryUomName: primary_uom_name
      })

      await fetchItems()
      return id
    } catch (e) {
      console.error('Failed to create item:', e)
      return null
    }
  }

  async function updateItem(id: string, label: string, unit: string) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    try {
      await invoke('update_item', {
        id,
        workspaceId: currentWorkspace.value.id,
        label,
        unit
      })
      await fetchItems()
    } catch (e) {
      console.error('Failed to update item:', e)
      throw e
    }
  }

  async function deleteItem(id: string) {
    if (!currentWorkspace.value) return
    try {
      await invoke('delete_item', {
        id,
        workspaceId: currentWorkspace.value.id
      })
      await fetchItems()
    } catch (e) {
      console.error('Failed to delete item:', e)
    }
  }

  return {
    items,
    loading,
    fetchItems,
    createItem,
    updateItem,
    deleteItem
  }
}
