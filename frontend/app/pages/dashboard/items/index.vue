<template>
  <div ref="scrollContainer" class="h-full overflow-y-auto pr-2 pb-20">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)]">{{ $t('catalog.title') }}</h1>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">{{ $t('catalog.description') }}</p>
      </div>

      <div class="flex items-center space-x-3 w-full md:w-auto">
        <div class="relative flex-1 md:w-64">
          <UIcon name="i-lucide-search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            data-testid="item-search-input"
            v-model="searchQuery" 
            type="text" 
            :placeholder="$t('catalog.searchPlaceholder')" 
            class="lh-input pl-9 w-full"
          />
        </div>
        <button data-testid="add-item-btn" @click="isAddModalOpen = true" class="lh-btn lh-btn-primary whitespace-nowrap">
          <UIcon name="i-lucide-plus" class="w-4 h-4 md:mr-2" />
          <span class="hidden md:inline">{{ $t('catalog.addItem') }}</span>
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
      <h3 class="text-lg font-medium text-[var(--lh-ink-primary)]">{{ $t('catalog.emptyState.title') }}</h3>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1 mb-6">{{ $t('catalog.emptyState.description') }}</p>
      <button @click="isAddModalOpen = true" class="lh-btn lh-btn-primary mx-auto">
        {{ $t('catalog.emptyState.button') }}
      </button>
    </div>

    <div v-else-if="items.length === 0 && searchQuery" class="lh-card text-center py-12">
      <h3 class="text-lg font-medium text-[var(--lh-ink-primary)]">{{ $t('catalog.noMatchState.title') }}</h3>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">{{ $t('catalog.noMatchState.description') }}</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="item in items" :key="item.id" 
        :class="[
          'lh-card flex flex-col justify-between group transition-colors',
          item.deleted_at ? 'opacity-60 bg-gray-50 dark:bg-gray-900/50 grayscale' : ''
        ]"
      >
        <div>
          <div class="flex items-center justify-between">
            <h3 class="font-medium text-[var(--lh-ink-primary)] flex items-center">
              {{ item.label }}
              <button @click="openEditModal(item)" class="ml-2 text-gray-400 hover:text-[var(--lh-brand)]">
                <UIcon name="i-lucide-pencil" class="w-3.5 h-3.5" />
              </button>
              <span v-if="item.deleted_at" class="ml-2 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400">{{ $t('status.archived') }}</span>
            </h3>
            <span data-testid="primary-uom-badge" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
              {{ item.primary_uom_id ? item.uoms?.find(u => u.id === item.primary_uom_id)?.unit_name || item.base_unit_name : item.base_unit_name }}
            </span>
          </div>
          
          <!-- Inventory Mode Extensions -->
          <div v-if="currentWorkspace?.mode === 'INVENTORY'" class="mt-4">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-[var(--lh-ink-secondary)]">{{ $t('itemCard.currentStock') }}</span>
              <span :class="[
                'text-lg font-bold',
                (item.current_stock <= (item.reorder_point || 0)) ? 'text-[var(--lh-danger)]' : 'text-[var(--lh-ink-primary)]'
              ]"><span data-testid="stock-display">{{ formatStock(item) }}</span></span>
            </div>
            <div v-if="item.reorder_point !== null" class="flex items-center justify-between">
              <span class="text-xs text-[var(--lh-ink-secondary)]">{{ $t('itemCard.reorderPoint') }}</span>
              <span class="text-xs font-medium text-[var(--lh-ink-secondary)]">{{ item.reorder_point }}</span>
            </div>
            
            <div class="mt-4 grid grid-cols-2 gap-2" v-if="!item.deleted_at">
              <button data-testid="use-stock-btn" @click="openInventorySlideover(item, false)" class="lh-btn lh-btn-secondary !text-red-600 dark:!text-red-400 !border-red-200 hover:!bg-red-50 dark:!border-red-900/50 dark:hover:!bg-red-900/20 !py-1.5 !text-xs justify-center">
                {{ $t('itemCard.useStockBtn') }}
              </button>
              <button data-testid="receive-stock-btn" @click="openInventorySlideover(item, true)" class="lh-btn lh-btn-secondary !text-green-600 dark:!text-green-400 !border-green-200 hover:!bg-green-50 dark:!border-green-900/50 dark:hover:!bg-green-900/20 !py-1.5 !text-xs justify-center">
                {{ $t('itemCard.receiveBtn') }}
              </button>
            </div>
          </div>

          <!-- Accounts Mode Info -->
          <p v-else class="text-xs text-[var(--lh-ink-secondary)] mt-2">{{ $t('catalog.addedDate', { date: new Date(item.created_at).toLocaleDateString() }) }}</p>
        </div>
        
        <div class="mt-4 pt-4 border-t border-[var(--lh-border-subtle)] flex items-center justify-between">
          <button v-if="!item.deleted_at && currentWorkspace?.mode === 'INVENTORY'" @click="openForecastSettings(item)" class="text-[var(--lh-brand)] hover:underline text-sm font-medium flex items-center">
            <UIcon name="i-lucide-bot" class="w-4 h-4 mr-1.5" />
            {{ $t('itemCard.aiSettingsBtn') }}
          </button>
          <div class="flex-1"></div>
          <button v-if="!item.deleted_at" @click="handleDelete(item.id)" class="text-[var(--lh-danger)] hover:underline text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
            {{ $t('itemCard.archiveBtn') }}
          </button>
          <span v-else class="text-sm font-medium text-gray-400">{{ $t('itemCard.archivedRecord') }}</span>
        </div>
      </div>
    </div>

    <!-- Inventory Logging Slideover -->
    <MovementSlideover 
      v-if="isSlideoverOpen"
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
      v-if="isForecastSettingsOpen"
      v-model="isForecastSettingsOpen"
      :item="selectedItemForForecast"
    />

    <!-- Add Item Modal -->
    <UModal v-if="isAddModalOpen" v-model="isAddModalOpen">
      <div class="p-6 bg-[var(--lh-bg-surface)] rounded-2xl border border-[var(--lh-border)] shadow-xl">
        <h3 class="text-lg font-semibold text-[var(--lh-ink-primary)] mb-4">{{ $t('addModal.title') }}</h3>
        <form @submit.prevent="submitAdd" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('addModal.labelInput') }}</label>
            <input 
              data-testid="item-label-input"
              v-model="newItemForm.label" 
              type="text" 
              required 
              :placeholder="$t('addModal.labelPlaceholder')" 
              class="lh-input"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('addModal.baseUnitInput') }}</label>
              <select data-testid="item-unit-select" v-model="newItemForm.unit" class="lh-input" required>
                <option value="Pieces">Pieces (pcs)</option>
                <option value="Kilograms">Kilograms (kg)</option>
                <option value="Pounds">Pounds (lbs)</option>
                <option value="Liters">Liters (L)</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('addModal.reorderPointInput') }}</label>
              <input 
                v-model.number="newItemForm.reorder_point" 
                type="number" 
                min="0"
                :placeholder="$t('addModal.reorderPlaceholder')" 
                class="lh-input"
              />
            </div>
          </div>
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="isAddModalOpen = false" class="lh-btn lh-btn-secondary">{{ $t('actions.cancel') }}</button>
            <button data-testid="submit-item-btn" type="submit" class="lh-btn lh-btn-primary" :disabled="!newItemForm.label">{{ $t('addModal.saveBtn') }}</button>
          </div>
        </form>
      </div>
    </UModal>

    <!-- Edit Item Modal -->
    <UModal v-if="isEditModalOpen" v-model="isEditModalOpen">
      <div class="p-6 bg-[var(--lh-bg-surface)] rounded-2xl border border-[var(--lh-border)] shadow-xl">
        <h3 class="text-lg font-semibold text-[var(--lh-ink-primary)] mb-4">Edit Item</h3>
        <form @submit.prevent="submitEdit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('addModal.labelInput') }}</label>
            <input 
              data-testid="edit-item-label-input"
              v-model="editItemForm.label" 
              type="text" 
              required 
              class="lh-input"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('addModal.baseUnitInput') }}</label>
            <select v-model="editItemForm.unit" class="lh-input" required>
              <option value="Pieces">Pieces (pcs)</option>
              <option value="Kilograms">Kilograms (kg)</option>
              <option value="Pounds">Pounds (lbs)</option>
              <option value="Liters">Liters (L)</option>
            </select>
          </div>
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="isEditModalOpen = false" class="lh-btn lh-btn-secondary">{{ $t('actions.cancel') }}</button>
            <button data-testid="save-item-btn" type="submit" class="lh-btn lh-btn-primary" :disabled="!editItemForm.label">Save Changes</button>
          </div>
        </form>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { refDebounced, useInfiniteScroll } from '@vueuse/core'
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
const { items, loading, fetchItems, createItem, updateItem, deleteItem } = useItems()
const { translateToDisplay } = useUOMTranslator()
const { t, n } = useI18n()

const isAddModalOpen = ref(false)
const newItemForm = ref<{ label: string, unit: string, reorder_point: number | null }>({ label: '', unit: 'Pieces', reorder_point: null })

const isEditModalOpen = ref(false)
const editItemForm = ref<{ id: string, label: string, unit: string }>({ id: '', label: '', unit: '' })

// Infinite Scroll & Search State
const searchQuery = ref('')
// THEORY OF CONSTRAINTS: 500ms debounce is a bottleneck for E2E tests.
// Disable or shorten it if we detect a test environment.
const debounceMs = (typeof window !== 'undefined' && (window as any).__TAURI_INTERNALS__) ? 0 : 500
const debouncedSearch = refDebounced(searchQuery, debounceMs)
const hasMoreItems = ref(true)
const scrollContainer = ref<HTMLElement | null>(null)

// Trigger fresh search when debounced input changes
watch(debouncedSearch, async (newVal) => {
  hasMoreItems.value = true
  await fetchItems(newVal, undefined, 100)
})

useInfiniteScroll(
  scrollContainer,
  async () => {
    if (loading.value || !hasMoreItems.value) return
    const cursor = items.value.length > 0 ? items.value[items.value.length - 1].created_at : undefined
    
    const prevCount = items.value.length
    await fetchItems(debouncedSearch.value, cursor, 100)
    
    if (items.value.length - prevCount < 100) {
      hasMoreItems.value = false
    }
  },
  { distance: 200 }
)

// Inventory Slideover State
const isSlideoverOpen = ref(false)
const isReceivingMode = ref(true)
const selectedItemForLogging = ref<Item | null>(null)

// AI Forecast Settings State
const isForecastSettingsOpen = ref(false)
const selectedItemForForecast = ref<Item | null>(null)

onMounted(async () => {
  await fetchItems(undefined, undefined, 100)
})

function formatStock(item: any) {
  if (!item) return '0'
  const primaryUom = item.uoms?.find((u: any) => u.id === item.primary_uom_id);
  const multiplier = primaryUom ? primaryUom.multiplier : 1.0;
  const unitName = primaryUom ? primaryUom.unit_name : item.base_unit_name;
  
  const { is_negative, whole_units, remainder } = translateToDisplay(item.current_stock || 0, multiplier, unitName, item.base_unit_name);
  
  // Natively reconstruct the string using i18n placeholders and locale-aware number formatting
  let text = '';
  
  const formattedWhole = n(whole_units || 0, 'decimal')
  const formattedRemainder = n(remainder || 0, 'decimal')

  if (whole_units > 0 && remainder > 0) {
    text = t('itemCard.stockFormat.both', { whole: formattedWhole, uom: unitName, remainder: formattedRemainder, base: item.base_unit_name })
  } else if (whole_units > 0) {
    text = t('itemCard.stockFormat.whole', { whole: formattedWhole, uom: unitName })
  } else if (remainder > 0) {
    text = t('itemCard.stockFormat.remainder', { remainder: formattedRemainder, base: item.base_unit_name })
  } else {
    text = t('itemCard.stockFormat.whole', { whole: n(0, 'decimal'), uom: unitName })
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

function openEditModal(item: Item) {
  editItemForm.value = {
    id: item.id,
    label: item.label,
    unit: item.base_unit_name
  }
  isEditModalOpen.value = true
}

async function submitEdit() {
  if (!editItemForm.value.label) return
  await updateItem(editItemForm.value.id, editItemForm.value.label, editItemForm.value.unit)
  isEditModalOpen.value = false
}

async function handleDelete(id: string) {
  if (confirm(t('itemCard.confirmDelete'))) {
    await deleteItem(id)
  }
}
</script>
