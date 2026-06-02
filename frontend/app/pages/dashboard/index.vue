<template>
  <div v-if="loading" class="flex items-center justify-center h-64">
    <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-[var(--lh-brand)] animate-spin" />
  </div>
  
  <div v-else-if="currentWorkspace">
    <div class="mb-8">
      <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)]">
        {{ currentWorkspace.name }} Dashboard
      </h1>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">
        Currently operating in {{ currentWorkspace.mode === 'ACCOUNTS' ? 'Accounts Mode' : 'Inventory Mode' }}
      </p>
    </div>

    <!-- Accounts Mode Dashboard -->
    <div v-if="currentWorkspace.mode === 'ACCOUNTS'" class="space-y-6 flex flex-col h-full">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 shrink-0">
        <!-- Quick Stat Cards -->
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Total Ledger Movements</div>
          <div class="text-3xl font-semibold text-[var(--lh-ink-primary)]">{{ totalMovements }}</div>
        </div>
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Pending Corrective Actions</div>
          <div class="text-3xl font-semibold text-[var(--lh-warning)]">0</div>
        </div>
      </div>
      
      <!-- Virtualized Global Ledger (Shared) -->
      <div class="lh-card flex flex-col flex-1 min-h-[400px]">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="font-medium text-[var(--lh-ink-primary)]">Global Accounts Ledger</h2>
            <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Real-time virtualized view of all client movements.</p>
          </div>
        </div>
        
        <div v-bind="containerProps" class="flex-1 overflow-y-auto border border-[var(--lh-border-subtle)] rounded-lg bg-[var(--lh-bg-surface)]">
          <div v-bind="wrapperProps" class="divide-y divide-[var(--lh-border-subtle)]">
            <div v-for="item in list" :key="item.index" class="p-4 hover:bg-[var(--lh-bg-subtle)] transition-colors flex items-center justify-between">
              <template v-if="item.data">
                <div>
                  <span class="text-xs text-[var(--lh-ink-secondary)]">{{ item.data.timestamp ? new Date(item.data.timestamp).toLocaleString() : '--' }}</span>
                  <div class="font-medium text-[var(--lh-ink-primary)]">{{ item.data.item_label || 'Unknown Item' }}</div>
                </div>
                <div class="flex items-center space-x-4">
                  <div class="text-sm text-[var(--lh-ink-secondary)] max-w-[200px] truncate">
                    {{ item.data.notes || '--' }}
                  </div>
                  <div :class="[
                    'px-2 py-1 rounded text-xs font-medium w-20 text-center',
                    item.data.direction === 'SEND' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                  ]">
                    {{ item.data.direction === 'SEND' ? '+' : '-' }}{{ item.data.quantity || 0 }}
                  </div>
                </div>
              </template>
            </div>
            <div v-if="globalHistory.length === 0" class="p-8 text-center text-[var(--lh-ink-secondary)] text-sm">
              No movements recorded yet.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Inventory Mode Dashboard -->
    <div v-else class="space-y-6 flex flex-col h-full">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 shrink-0">
        <!-- Quick Stat Cards -->
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Total Ledger Movements</div>
          <div class="text-3xl font-semibold text-[var(--lh-ink-primary)]">{{ totalMovements }}</div>
        </div>
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Low Stock Alerts</div>
          <div class="text-3xl font-semibold text-[var(--lh-warning)]">0</div>
        </div>
      </div>

      <!-- Virtualized Global Ledger (Shared) -->
      <div class="lh-card flex flex-col flex-1 min-h-[400px]">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="font-medium text-[var(--lh-ink-primary)]">Global Inventory Ledger</h2>
            <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Real-time virtualized view of all warehouse movements.</p>
          </div>
        </div>
        
        <div v-bind="containerProps" class="flex-1 overflow-y-auto border border-[var(--lh-border-subtle)] rounded-lg bg-[var(--lh-bg-surface)]">
          <div v-bind="wrapperProps" class="divide-y divide-[var(--lh-border-subtle)]">
            <div v-for="item in list" :key="item.index" class="p-4 hover:bg-[var(--lh-bg-subtle)] transition-colors flex items-center justify-between">
              <template v-if="item.data">
                <div>
                  <span class="text-xs text-[var(--lh-ink-secondary)]">{{ item.data.timestamp ? new Date(item.data.timestamp).toLocaleString() : '--' }}</span>
                  <div class="font-medium text-[var(--lh-ink-primary)]">{{ item.data.item_label || 'Unknown Item' }}</div>
                </div>
                <div class="flex items-center space-x-4">
                  <div class="text-sm text-[var(--lh-ink-secondary)] max-w-[200px] truncate">
                    {{ item.data.notes || '--' }}
                  </div>
                  <div :class="[
                    'px-2 py-1 rounded text-xs font-medium w-20 text-center',
                    item.data.direction === 'SEND' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                  ]">
                    {{ item.data.direction === 'SEND' ? '+' : '-' }}{{ item.data.quantity || 0 }}
                  </div>
                </div>
              </template>
            </div>
            <div v-if="globalHistory.length === 0" class="p-8 text-center text-[var(--lh-ink-secondary)] text-sm">
              No movements recorded yet.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useVirtualList, useInfiniteScroll } from '@vueuse/core'
import { useWorkspace } from '../../composables/useWorkspace'
import { useLedger } from '../../composables/useLedger'
import type { MovementHistoryRow } from '../../types/generated/MovementHistoryRow'

// Use the main app shell layout
definePageMeta({
  layout: 'default'
})

const router = useRouter()
const { currentWorkspace, loading, restoreActiveWorkspace } = useWorkspace()
const { fetchGlobalHistory, fetchHistoryCount, loading: ledgerLoading } = useLedger()

const globalHistory = ref<MovementHistoryRow[]>([])
const totalMovements = ref(0)
const hasMoreHistory = ref(true)

const { list, containerProps, wrapperProps } = useVirtualList(
  globalHistory,
  {
    itemHeight: 73 // Fixed height based on DOM inspection
  }
)

async function loadMoreHistory() {
  if (ledgerLoading.value || !hasMoreHistory.value) return
  
  const cursor = globalHistory.value.length > 0 
    ? globalHistory.value[globalHistory.value.length - 1].timestamp 
    : undefined
    
  const newRows = await fetchGlobalHistory(cursor)
  if (newRows.length < 100) {
    hasMoreHistory.value = false // We hit the end
  }
  
  if (newRows.length > 0) {
    globalHistory.value.push(...newRows)
  }
}

// Attach infinite scroll to the virtual list container
useInfiniteScroll(
  containerProps.ref,
  async () => {
    await loadMoreHistory()
  },
  { distance: 10 }
)

onMounted(async () => {
  await restoreActiveWorkspace()
  
  // THEORY OF CONSTRAINTS: Wait for workspace to be ready before initial fetch
  if (!currentWorkspace.value) {
    const unwatch = watch(() => currentWorkspace.value, async (newWs) => {
      if (newWs) {
        totalMovements.value = await fetchHistoryCount()
        await loadMoreHistory()
        unwatch()
      }
    })
  } else {
    totalMovements.value = await fetchHistoryCount()
    await loadMoreHistory()
  }
})
</script>
