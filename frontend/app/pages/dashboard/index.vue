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
    <div v-if="currentWorkspace.mode === 'ACCOUNTS'" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Quick Stat Cards -->
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Active Clients</div>
          <div class="text-3xl font-semibold text-[var(--lh-ink-primary)]">0</div>
        </div>
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Items Out</div>
          <div class="text-3xl font-semibold text-[var(--lh-ink-primary)]">0</div>
        </div>
      </div>

      <div class="lh-card">
        <h2 class="font-medium text-[var(--lh-ink-primary)] mb-4">Recent Activity</h2>
        <p class="text-sm text-[var(--lh-ink-secondary)]">No recent ledger activity.</p>
      </div>
    </div>

    <!-- Inventory Mode Dashboard -->
    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Quick Stat Cards -->
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Total Items Tracked</div>
          <div class="text-3xl font-semibold text-[var(--lh-ink-primary)]">0</div>
        </div>
        <div class="lh-card">
          <div class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-1">Low Stock Alerts</div>
          <div class="text-3xl font-semibold text-[var(--lh-warning)]">0</div>
        </div>
      </div>

      <div class="lh-card flex items-center justify-between">
        <div>
          <h2 class="font-medium text-[var(--lh-ink-primary)]">TimesFM Forecasting</h2>
          <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Predict future stock levels based on past usage.</p>
        </div>
        <button class="lh-btn lh-btn-secondary">
          <UIcon name="i-lucide-line-chart" class="w-4 h-4 mr-2 text-[var(--lh-brand)]" />
          Run Forecast
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspace } from '../../composables/useWorkspace'

// Use the main app shell layout
definePageMeta({
  layout: 'default'
})

const router = useRouter()
const { currentWorkspace, loading, restoreActiveWorkspace } = useWorkspace()

onMounted(async () => {
  await restoreActiveWorkspace()
  
  if (!currentWorkspace.value) {
    // Security check: if they somehow landed here without an active workspace, kick them out
    router.replace('/')
  }
})
</script>
