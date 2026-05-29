<template>
  <div>
    <!-- Navigation & Header -->
    <div class="mb-8">
      <NuxtLink to="/dashboard/clients" class="inline-flex items-center text-sm font-medium text-[var(--lh-ink-secondary)] hover:text-[var(--lh-brand)] mb-4 transition-colors">
        <UIcon name="i-lucide-arrow-left" class="w-4 h-4 mr-1" />
        Back to Clients
      </NuxtLink>
      
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)] flex items-center">
            {{ client?.name || 'Loading...' }}
          </h1>
          <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Client Ledger & History</p>
        </div>
        
        <div class="flex items-center space-x-3">
          <button @click="openSlideover(false)" class="lh-btn lh-btn-secondary !text-green-600 dark:!text-green-400 !border-green-200 hover:!bg-green-50 dark:!border-green-900/50 dark:hover:!bg-green-900/20">
            <UIcon name="i-lucide-arrow-down-to-line" class="w-4 h-4 mr-2" />
            Log Return
          </button>
          <button @click="openSlideover(true)" class="lh-btn lh-btn-primary">
            <UIcon name="i-lucide-send" class="w-4 h-4 mr-2" />
            Send Items
          </button>
        </div>
      </div>
    </div>

    <!-- Live Balances -->
    <div class="lh-card mb-8">
      <h2 class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-4 uppercase tracking-wider">Current Outstanding Balance</h2>
      
      <div v-if="loading" class="flex justify-center py-4">
        <UIcon name="i-lucide-loader-2" class="w-6 h-6 text-[var(--lh-brand)] animate-spin" />
      </div>
      
      <div v-else-if="balances.length === 0" class="text-sm text-[var(--lh-ink-secondary)] py-2">
        This client currently holds no items.
      </div>
      
      <div v-else class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div v-for="bal in balances" :key="bal.item_id" class="p-4 rounded-xl bg-[var(--lh-bg-subtle)] border border-[var(--lh-border-subtle)]">
          <div class="text-2xl font-semibold text-[var(--lh-ink-primary)] mb-1">{{ bal.balance }}</div>
          <div class="text-sm font-medium text-[var(--lh-ink-primary)] truncate">{{ bal.label }}</div>
          <div class="text-xs text-[var(--lh-ink-secondary)]">{{ bal.unit }}</div>
        </div>
      </div>
    </div>

    <!-- History Log -->
    <div class="lh-card">
      <h2 class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-4 uppercase tracking-wider">Transaction History</h2>
      
      <div v-if="history.length === 0" class="text-center py-8">
        <div class="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-3">
          <UIcon name="i-lucide-history" class="w-6 h-6 text-gray-400" />
        </div>
        <p class="text-sm text-[var(--lh-ink-secondary)]">No transactions recorded for this client yet.</p>
      </div>
      
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-[var(--lh-border-subtle)] text-[var(--lh-ink-secondary)]">
              <th class="font-medium py-3 px-4">Date</th>
              <th class="font-medium py-3 px-4">Direction</th>
              <th class="font-medium py-3 px-4">Item</th>
              <th class="font-medium py-3 px-4 text-right">Qty</th>
              <th class="font-medium py-3 px-4">Notes / Exceptions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--lh-border-subtle)]">
            <tr v-for="row in history" :key="row.id + row.item_label" class="hover:bg-[var(--lh-bg-subtle)] transition-colors">
              <td class="py-3 px-4 text-[var(--lh-ink-primary)] whitespace-nowrap">
                {{ new Date(row.timestamp).toLocaleString() }}
              </td>
              <td class="py-3 px-4">
                <span :class="[
                  'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                  row.direction === 'SEND' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                ]">
                  {{ row.direction }}
                </span>
              </td>
              <td class="py-3 px-4 text-[var(--lh-ink-primary)]">{{ row.item_label }}</td>
              <td class="py-3 px-4 text-right font-medium text-[var(--lh-ink-primary)]">
                {{ row.direction === 'SEND' ? '+' : '-' }}{{ row.quantity }}
              </td>
              <td class="py-3 px-4 text-[var(--lh-ink-secondary)] text-xs">
                <div v-if="row.correction_reason" class="text-amber-600 dark:text-amber-400 font-medium mb-0.5">
                  EXCEPTION: {{ row.correction_reason }}
                </div>
                <div>{{ row.notes || '--' }}</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Movement Slideover -->
    <MovementSlideover 
      v-model="isSlideoverOpen"
      :client-id="clientId"
      :client-name="client?.name || ''"
      :is-sending="isSendingMode"
      @success="handleMovementSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDatabase } from '../../../composables/useDatabase'
import { useLedger, type MovementHistoryRow } from '../../../composables/useLedger'
import type { Client } from '../../../types/domain'
import MovementSlideover from '../../../components/ledger/MovementSlideover.vue'

definePageMeta({
  layout: 'default'
})

const route = useRoute()
const clientId = route.params.id as string

const { fetchClientHistory } = useLedger()

// State
const client = ref<Client | null>(null)
const loading = ref(true)
const history = ref<MovementHistoryRow[]>([])
const balances = ref<Array<{ item_id: string, label: string, unit: string, balance: number }>>([])

// Slideover state
const isSlideoverOpen = ref(false)
const isSendingMode = ref(true)

async function loadData() {
  loading.value = true
  try {
    const db = await useDatabase()
    
    // 1. Fetch Client Details
    const clientResult = await db.select<Client[]>('SELECT * FROM clients WHERE id = $1', [clientId])
    if (clientResult.length > 0) {
      client.value = clientResult[0] || null
    }

    // 2. Fetch Live Balances grouping by item
    // A SEND is positive. A COLLECT is negative.
    const balanceQuery = `
      SELECT 
        i.id as item_id,
        i.label,
        i.unit,
        SUM(
          CASE 
            WHEN m.direction = 'SEND' THEN mli.quantity
            WHEN m.direction = 'COLLECT' THEN -mli.quantity
            ELSE 0 
          END
        ) as balance
      FROM items i
      JOIN movement_line_items mli ON i.id = mli.item_id
      JOIN movements m ON mli.movement_id = m.id
      WHERE m.client_id = $1
      GROUP BY i.id
      HAVING balance > 0
      ORDER BY i.label ASC
    `
    balances.value = await db.select<typeof balances.value>(balanceQuery, [clientId])

    // 3. Fetch Chronological History
    history.value = await fetchClientHistory(clientId)

  } catch (e) {
    console.error('Failed to load client details:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

function openSlideover(isSending: boolean) {
  isSendingMode.value = isSending
  isSlideoverOpen.value = true
}

function handleMovementSuccess() {
  // Reload data to reflect the new balances and history
  loadData()
}
</script>
