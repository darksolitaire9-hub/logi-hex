<template>
  <div>
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)]">Item Catalog</h1>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Manage the predefined items you track in this workspace.</p>
      </div>

      <div class="flex items-center space-x-3 w-full md:w-auto">
        <div class="relative flex-1 md:w-64">
          <UIcon name="i-lucide-search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            data-testid="item-search-input"
            v-model="searchQuery" 
            type="text" 
            placeholder="Search items..." 
            class="lh-input pl-9 w-full"
          />
        </div>
        <button data-testid="add-item-btn" @click="isAddModalOpen = true" class="lh-btn lh-btn-primary whitespace-nowrap">
          <UIcon name="i-lucide-plus" class="w-4 h-4 md:mr-2" />
          <span class="hidden md:inline">Add Item</span>
        </button>
      </div>
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

    <div v-else-if="filteredItems.length === 0" class="lh-card text-center py-12">
      <h3 class="text-lg font-medium text-[var(--lh-ink-primary)]">No items match your search</h3>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Try a different label or filter.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="item in filteredItems" :key="item.id" 
        :class="[
          'lh-card flex flex-col justify-between group transition-colors',
          item.deleted_at ? 'opacity-60 bg-gray-50 dark:bg-gray-900/50 grayscale' : ''
        ]"
      >
        <div>
          <div class="flex items-center justify-between">
            <h3 class="font-medium text-[var(--lh-ink-primary)] flex items-center">
              {{ item.label }}
              <span v-if="item.deleted_at" class="ml-2 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400">Archived</span>
            </h3>
            <span data-testid="primary-uom-badge" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
              {{ item.primary_uom_id ? item.uoms?.find(u => u.id === item.primary_uom_id)?.unit_name || item.base_unit_name : item.base_unit_name }}
            </span>
          </div>
          
          <!-- Inventory Mode Extensions -->
          <div v-if="currentWorkspace?.mode === 'INVENTORY'" class="mt-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-[var(--lh-ink-secondary)]">Current Stock</span>
              <span :class="[
                'text-lg font-bold',
                (item.current_stock <= (item.reorder_point || 0)) ? 'text-[var(--lh-danger)]' : 'text-[var(--lh-ink-primary)]'
              ]"><span data-testid="stock-display">{{ formatStock(item) }}</span></span>
            </div>
            <div v-if="item.reorder_point !== null" class="flex items-center justify-between">
              <span class="text-xs text-[var(--lh-ink-secondary)]">Reorder Point</span>
              <span class="text-xs font-medium text-[var(--lh-ink-secondary)]">{{ item.reorder_point }}</span>
            </div>
            
            <div class="mt-4 grid grid-cols-2 gap-2" v-if="!item.deleted_at">
              <button data-testid="use-stock-btn" @click="openInventorySlideover(item, false)" class="lh-btn lh-btn-secondary !text-red-600 dark:!text-red-400 !border-red-200 hover:!bg-red-50 dark:!border-red-900/50 dark:hover:!bg-red-900/20 !py-1.5 !text-xs justify-center">
                Use Stock
              </button>
              <button data-testid="receive-stock-btn" @click="openInventorySlideover(item, true)" class="lh-btn lh-btn-secondary !text-green-600 dark:!text-green-400 !border-green-200 hover:!bg-green-50 dark:!border-green-900/50 dark:hover:!bg-green-900/20 !py-1.5 !text-xs justify-center">
                Receive
              </button>
            </div>
          </div>

          <!-- Accounts Mode Info -->
          <p v-else class="text-xs text-[var(--lh-ink-secondary)] mt-2">Added {{ new Date(item.created_at).toLocaleDateString() }}</p>
        </div>
        
        <div class="mt-4 pt-4 border-t border-[var(--lh-border-subtle)] flex items-center justify-between">
          <button v-if="!item.deleted_at && currentWorkspace?.mode === 'INVENTORY'" @click="openForecastSettings(item)" class="text-[var(--lh-brand)] hover:underline text-sm font-medium flex items-center">
            <UIcon name="i-lucide-bot" class="w-4 h-4 mr-1.5" />
            AI Settings
          </button>
          <div class="flex-1"></div>
          <button v-if="!item.deleted_at" @click="handleDelete(item.id)" class="text-[var(--lh-danger)] hover:underline text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
            Archive
          </button>
          <span v-else class="text-sm font-medium text-gray-400">Archived Record</span>
        </div>
      </div>
    </div>

    <!-- Inventory Logging Slideover -->
    <MovementSlideover 
      v-model="isSlideoverOpen"
      :client-id="''"
      :client-name="'Internal Warehouse'"
      :is-sending="!isReceivingMode"
      :force-direction="isReceivingMode ? 'RECEIVE' : 'USE'"
      :pre-select-item="selectedItemForLogging?.id"
      @success="handleInventorySuccess"
    />

    <!-- AI Forecast Settings Slideover -->
    <ForecastSettingsSlideover
      v-model="isForecastSettingsOpen"
      :item="selectedItemForForecast"
    />

    <!-- Add Item Modal -->
    <UModal v-model="isAddModalOpen">
      <div class="p-6 bg-[var(--lh-bg-surface)] rounded-2xl border border-[var(--lh-border)] shadow-xl">
        <h3 class="text-lg font-semibold text-[var(--lh-ink-primary)] mb-4">Add New Item</h3>
        <form @submit.prevent="submitAdd" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Item Label</label>
            <input 
              data-testid="item-label-input"
              v-model="newItemForm.label" 
              type="text" 
              required 
              placeholder="e.g., Euro Pallet" 
              class="lh-input"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Base Unit of Measure</label>
              <select v-model="newItemForm.unit" class="lh-input" required>
                <option value="Pieces">Pieces (pcs)</option>
                <option value="Kilograms">Kilograms (kg)</option>
                <option value="Pounds">Pounds (lbs)</option>
                <option value="Liters">Liters (L)</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Reorder Point</label>
              <input 
                v-model.number="newItemForm.reorder_point" 
                type="number" 
                min="0"
                placeholder="Alert Threshold" 
                class="lh-input"
              />
            </div>
          </div>
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="isAddModalOpen = false" class="lh-btn lh-btn-secondary">Cancel</button>
            <button data-testid="submit-item-btn" type="submit" class="lh-btn lh-btn-primary" :disabled="!newItemForm.label">Save Item</button>
          </div>
        </form>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useWorkspace } from '../../../composables/useWorkspace'
import { useItems } from '../../../composables/useItems'
import { useUOMTranslator } from '../../../composables/useUOMTranslator'
import type { Item } from '../../../types/domain'
import MovementSlideover from '../../../components/ledger/MovementSlideover.vue'
import ForecastSettingsSlideover from '../../../components/forecasting/ForecastSettingsSlideover.vue'

definePageMeta({
  layout: 'default'
})

const { currentWorkspace } = useWorkspace()
const { items, loading, fetchItems, createItem, deleteItem } = useItems()
const { translateToDisplay } = useUOMTranslator()

const isAddModalOpen = ref(false)
const newItemForm = ref<{ label: string, unit: string, reorder_point: number | null }>({ label: '', unit: 'Pieces', reorder_point: null })

const searchQuery = ref('')
const filteredItems = computed(() => {
  if (!searchQuery.value) return items.value
  const q = searchQuery.value.toLowerCase()
  return items.value.filter(i => i.label.toLowerCase().includes(q))
})

// Inventory Slideover State
const isSlideoverOpen = ref(false)
const isReceivingMode = ref(true)
const selectedItemForLogging = ref<Item | null>(null)

// AI Forecast Settings State
const isForecastSettingsOpen = ref(false)
const selectedItemForForecast = ref<Item | null>(null)

onMounted(async () => {
  await fetchItems()
})

function formatStock(item: any) {
  const primaryUom = item.uoms?.find((u: any) => u.id === item.primary_uom_id);
  const multiplier = primaryUom ? primaryUom.multiplier : 1.0;
  const unitName = primaryUom ? primaryUom.unit_name : item.base_unit_name;
  
  const { is_negative, whole_units, remainder } = translateToDisplay(item.current_stock, multiplier, unitName, item.base_unit_name);
  
  // Natively reconstruct the string (Later, this will be handled by $t('uom.stock_format', {...}))
  let text = '';
  if (whole_units > 0 && remainder > 0) {
    text = `${whole_units} ${unitName}, ${remainder} ${item.base_unit_name}`
  } else if (whole_units > 0) {
    text = `${whole_units} ${unitName}`
  } else if (remainder > 0) {
    text = `${remainder} ${item.base_unit_name}`
  } else {
    text = `0 ${unitName}`
  }

  return is_negative ? `-${text}` : text;
}

function openInventorySlideover(item: Item, receiving: boolean) {
  selectedItemForLogging.value = item
  isReceivingMode.value = receiving
  isSlideoverOpen.value = true
}

function openForecastSettings(item: Item) {
  selectedItemForForecast.value = item
  isForecastSettingsOpen.value = true
}

function handleInventorySuccess() {
  fetchItems()
}

async function submitAdd() {
  if (!newItemForm.value.label) return
  await createItem(newItemForm.value.label, newItemForm.value.unit, newItemForm.value.reorder_point)
  newItemForm.value = { label: '', unit: 'Pieces', reorder_point: null }
  isAddModalOpen.value = false
}

async function handleDelete(id: string) {
  if (confirm('Are you sure you want to delete this item? This may break historical records if it was used in movements.')) {
    await deleteItem(id)
  }
}
</script>
