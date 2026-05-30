import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { useDatabase } from './useDatabase'
import { useWorkspace } from './useWorkspace'
import { encryptField, decryptField } from '../utils/crypto'
import type { Item } from '../types/domain'

export function useItems() {
  const items = ref<Item[]>([])
  const loading = ref(false)
  const { currentWorkspace, activeCryptoKey } = useWorkspace()

  async function fetchItems() {
    if (!currentWorkspace.value) return
    loading.value = true
    try {
      const db = await useDatabase()
      const result = await db.select<Item[]>(
        `SELECT * FROM items 
         WHERE workspace_id = $1 
         ORDER BY 
           CASE WHEN deleted_at IS NULL THEN 0 ELSE 1 END ASC,
           created_at DESC`,
        [currentWorkspace.value.id]
      )
      
      const uoms = await db.select<any[]>(
        `SELECT * FROM item_uoms WHERE item_id IN (SELECT id FROM items WHERE workspace_id = $1)`,
        [currentWorkspace.value.id]
      )
      
      for (const item of result) {
        item.label = await decryptField(item.label, activeCryptoKey.value)
        item.uoms = uoms.filter(u => u.item_id === item.id)
      }
      
      items.value = result
    } catch (e) {
      console.error('Failed to fetch items:', e)
    } finally {
      loading.value = false
    }
  }

  async function createItem(label: string, base_unit_name: string, reorder_point: number | null = null, alternate_uoms: Array<{unit_name: string, multiplier: number}> = [], primary_uom_name: string | null = null) {
    if (!currentWorkspace.value) return null
    try {
      const db = await useDatabase()
      const id = uuidv4()
      const encryptedLabel = await encryptField(label, activeCryptoKey.value)
      
      // Step 1: Insert item with base identity
      await db.execute(
        'INSERT INTO items (id, workspace_id, label, unit, reorder_point, base_unit_name) VALUES ($1, $2, $3, $4, $5, $6)',
        [id, currentWorkspace.value.id, encryptedLabel, base_unit_name, reorder_point, base_unit_name]
      )

      // Step 2: Insert 1.0 Base UOM explicitly to solve the Identity Flaw
      const baseUomId = uuidv4()
      await db.execute(
        'INSERT INTO item_uoms (id, item_id, unit_name, multiplier) VALUES ($1, $2, $3, $4)',
        [baseUomId, id, base_unit_name, 1.0]
      )

      // Step 3: Insert alternates
      let primaryIdToSet = baseUomId;
      for (const uom of alternate_uoms) {
        const uomId = uuidv4()
        await db.execute(
          'INSERT INTO item_uoms (id, item_id, unit_name, multiplier) VALUES ($1, $2, $3, $4)',
          [uomId, id, uom.unit_name, uom.multiplier]
        )
        if (primary_uom_name === uom.unit_name) {
          primaryIdToSet = uomId;
        }
      }

      // Step 4: Set the Primary UOM
      await db.execute(
        'UPDATE items SET primary_uom_id = $1 WHERE id = $2',
        [primaryIdToSet, id]
      )

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
    if (!currentWorkspace.value) return
    try {
      const db = await useDatabase()
      // Enterprise Audit Trail: Soft Delete instead of DELETE FROM
      await db.execute(
        'UPDATE items SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND workspace_id = $2',
        [id, currentWorkspace.value.id]
      )
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
