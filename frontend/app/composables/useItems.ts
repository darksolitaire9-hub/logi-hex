import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import type { Item } from '../types/domain'

export function useItems() {
  const items = ref<Item[]>([])
  const loading = ref(false)
  const { currentWorkspace } = useWorkspace()

  async function fetchItems() {
    if (!currentWorkspace.value) return
    loading.value = true
    try {
      const db = await useDatabase()
      const result = await db.select<Item[]>(
        'SELECT * FROM items WHERE workspace_id = $1 ORDER BY label ASC',
        [currentWorkspace.value.id]
      )
      items.value = result
    } catch (e) {
      console.error('Failed to fetch items:', e)
    } finally {
      loading.value = false
    }
  }

  async function createItem(label: string, unit: string) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    try {
      const db = await useDatabase()
      const newId = uuidv4()
      await db.execute(
        'INSERT INTO items (id, workspace_id, label, unit) VALUES ($1, $2, $3, $4)',
        [newId, currentWorkspace.value.id, label, unit]
      )
      await fetchItems()
      return newId
    } catch (e) {
      console.error('Failed to create item:', e)
      throw e
    }
  }

  async function updateItem(id: string, label: string, unit: string) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    try {
      const db = await useDatabase()
      await db.execute(
        'UPDATE items SET label = $1, unit = $2 WHERE id = $3 AND workspace_id = $4',
        [label, unit, id, currentWorkspace.value.id]
      )
      await fetchItems()
    } catch (e) {
      console.error('Failed to update item:', e)
      throw e
    }
  }

  async function deleteItem(id: string) {
    if (!currentWorkspace.value) throw new Error('No active workspace')
    try {
      const db = await useDatabase()
      await db.execute(
        'DELETE FROM items WHERE id = $1 AND workspace_id = $2',
        [id, currentWorkspace.value.id]
      )
      await fetchItems()
    } catch (e) {
      console.error('Failed to delete item:', e)
      throw e
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
