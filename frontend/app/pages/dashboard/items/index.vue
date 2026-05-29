<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)]">Item Catalog</h1>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Manage the predefined items you track in this workspace.</p>
      </div>
      <button @click="isAddModalOpen = true" class="lh-btn lh-btn-primary">
        <UIcon name="i-lucide-plus" class="w-4 h-4 mr-2" />
        Add Item
      </button>
    </div>

    <!-- Items Grid -->
    <div v-if="loading && items.length === 0" class="flex justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-[var(--lh-brand)] animate-spin" />
    </div>

    <div v-else-if="items.length === 0" class="lh-card text-center py-12">
      <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
        <UIcon name="i-lucide-package-open" class="w-8 h-8 text-gray-400" />
      </div>
      <h3 class="text-lg font-medium text-[var(--lh-ink-primary)]">No items defined</h3>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1 mb-6">Create your first trackable item (e.g., Pallet, Crate, IBC Tote) to start sending them to clients.</p>
      <button @click="isAddModalOpen = true" class="lh-btn lh-btn-primary mx-auto">
        Create First Item
      </button>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="item in items" :key="item.id" class="lh-card flex flex-col justify-between group">
        <div>
          <div class="flex items-center justify-between">
            <h3 class="font-medium text-[var(--lh-ink-primary)]">{{ item.label }}</h3>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
              {{ item.unit }}
            </span>
          </div>
          <!-- In Accounts mode we just show that it exists. No local stock tracking. -->
          <p class="text-xs text-[var(--lh-ink-secondary)] mt-2">Added {{ new Date(item.created_at).toLocaleDateString() }}</p>
        </div>
        
        <div class="mt-4 pt-4 border-t border-[var(--lh-border-subtle)] flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
          <button @click="handleDelete(item.id)" class="text-[var(--lh-danger)] hover:underline text-sm font-medium">
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Add Item Modal -->
    <UModal v-model="isAddModalOpen">
      <div class="p-6 bg-[var(--lh-bg-surface)] rounded-2xl border border-[var(--lh-border)] shadow-xl">
        <h3 class="text-lg font-semibold text-[var(--lh-ink-primary)] mb-4">Add New Item</h3>
        <form @submit.prevent="submitAdd" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Item Label</label>
            <input 
              v-model="newItemForm.label" 
              type="text" 
              required 
              placeholder="e.g., Euro Pallet" 
              class="lh-input"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Unit of Measure</label>
            <select v-model="newItemForm.unit" class="lh-input" required>
              <option value="pcs">Pieces (pcs)</option>
              <option value="kg">Kilograms (kg)</option>
              <option value="lbs">Pounds (lbs)</option>
              <option value="liters">Liters (L)</option>
            </select>
          </div>
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="isAddModalOpen = false" class="lh-btn lh-btn-secondary">Cancel</button>
            <button type="submit" class="lh-btn lh-btn-primary" :disabled="!newItemForm.label">Save Item</button>
          </div>
        </form>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useItems } from '../../../composables/useItems'

definePageMeta({
  layout: 'default'
})

const { items, loading, fetchItems, createItem, deleteItem } = useItems()

const isAddModalOpen = ref(false)
const newItemForm = ref({ label: '', unit: 'pcs' })

onMounted(async () => {
  await fetchItems()
})

async function submitAdd() {
  if (!newItemForm.value.label) return
  await createItem(newItemForm.value.label, newItemForm.value.unit)
  newItemForm.value = { label: '', unit: 'pcs' }
  isAddModalOpen.value = false
}

async function handleDelete(id: string) {
  if (confirm('Are you sure you want to delete this item? This may break historical records if it was used in movements.')) {
    await deleteItem(id)
  }
}
</script>
