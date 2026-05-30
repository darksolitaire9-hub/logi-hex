<template>
  <div class="min-h-screen bg-[var(--lh-bg-base)] flex">
    <!-- Sidebar -->
    <aside class="w-64 border-r border-[var(--lh-border-subtle)] bg-[var(--lh-bg-surface)] flex flex-col hidden md:flex">
      <!-- App Header -->
      <div class="h-16 flex items-center px-6 border-b border-[var(--lh-border-subtle)]">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
          <UIcon name="i-lucide-box" class="text-white w-4 h-4" />
        </div>
        <span class="font-semibold text-[var(--lh-ink-primary)]">Logi-Hex</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <NuxtLink to="/dashboard" class="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-[var(--lh-ink-primary)] bg-[var(--lh-bg-subtle)]">
          <UIcon name="i-lucide-layout-dashboard" class="w-5 h-5 mr-3 text-[var(--lh-brand)]" />
          Dashboard
        </NuxtLink>

        <!-- Dynamic Menu Items based on Mode -->
        <template v-if="currentWorkspace?.mode === 'ACCOUNTS'">
          <NuxtLink to="/dashboard/clients" class="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-[var(--lh-ink-secondary)] hover:bg-[var(--lh-bg-subtle)] hover:text-[var(--lh-ink-primary)] transition-colors">
            <UIcon name="i-lucide-users" class="w-5 h-5 mr-3" />
            Clients
          </NuxtLink>
        </template>
        
        <template v-if="currentWorkspace?.mode === 'INVENTORY'">
          <NuxtLink to="/dashboard/items" class="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-[var(--lh-ink-secondary)] hover:bg-[var(--lh-bg-subtle)] hover:text-[var(--lh-ink-primary)] transition-colors">
            <UIcon name="i-lucide-package" class="w-5 h-5 mr-3" />
            Stock Items
          </NuxtLink>
          <NuxtLink to="/dashboard/forecast" class="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-[var(--lh-ink-secondary)] hover:bg-[var(--lh-bg-subtle)] hover:text-[var(--lh-ink-primary)] transition-colors">
            <UIcon name="i-lucide-line-chart" class="w-5 h-5 mr-3" />
            Forecasting
          </NuxtLink>
        </template>
        <NuxtLink to="/dashboard/settings" class="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-[var(--lh-ink-secondary)] hover:bg-[var(--lh-bg-subtle)] hover:text-[var(--lh-ink-primary)] transition-colors mt-4">
          <UIcon name="i-lucide-settings" class="w-5 h-5 mr-3" />
          Settings
        </NuxtLink>
      </nav>

      <!-- User/Workspace Switcher Footer -->
      <div class="p-4 border-t border-[var(--lh-border-subtle)]">
        <div class="flex items-center">
          <div class="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center mr-3">
            <UIcon :name="currentWorkspace?.mode === 'ACCOUNTS' ? 'i-lucide-users' : 'i-lucide-building'" class="w-4 h-4 text-gray-500" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-[var(--lh-ink-primary)] truncate">
              {{ currentWorkspace?.name || 'Loading...' }}
            </p>
            <p class="text-xs text-[var(--lh-ink-secondary)] truncate">
              {{ currentWorkspace?.mode === 'ACCOUNTS' ? 'Accounts Mode' : 'Inventory Mode' }}
            </p>
          </div>
        </div>
        <div class="mt-3">
          <NuxtLink to="/" class="text-xs text-[var(--lh-brand)] hover:underline flex items-center">
            <UIcon name="i-lucide-lock" class="w-3 h-3 mr-1" /> Lock Workspace
          </NuxtLink>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden relative">
      <!-- Topbar -->
      <header class="h-16 border-b border-[var(--lh-border-subtle)] bg-[var(--lh-bg-surface)] flex items-center justify-between px-4 sm:px-6 lg:px-8">
        <div class="flex items-center md:hidden">
          <span class="font-semibold text-[var(--lh-ink-primary)]">Logi-Hex</span>
        </div>
        <div class="hidden md:block">
          <!-- Optional breadcrumbs or page title could go here -->
        </div>
        
        <!-- Action Center -->
        <div class="flex items-center space-x-4">
          <!-- Notification Bell -->
          <button 
            v-if="currentWorkspace?.mode === 'INVENTORY'"
            @click="isAlertsOpen = true" 
            class="relative p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <UIcon name="i-lucide-bell" class="w-5 h-5 text-[var(--lh-ink-secondary)]" />
            <!-- Notification Badge -->
            <span v-if="lowStockItems.length > 0" class="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-[var(--lh-danger)] rounded-full ring-2 ring-[var(--lh-bg-surface)] animate-pulse"></span>
          </button>
        </div>
      </header>
      
      <!-- Page View -->
      <div class="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
        <div class="max-w-7xl mx-auto">
          <slot />
        </div>
      </div>

      <!-- Alerts Slideover -->
      <USlideover v-model="isAlertsOpen">
        <div class="flex flex-col h-full bg-[var(--lh-bg-surface)]">
          <div class="p-6 border-b border-[var(--lh-border-subtle)] flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-[var(--lh-ink-primary)] flex items-center">
                <UIcon name="i-lucide-alert-triangle" class="w-5 h-5 mr-2 text-[var(--lh-warning)]" />
                Action Required
              </h2>
              <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Items below safety stock threshold.</p>
            </div>
            <UButton color="neutral" variant="ghost" icon="i-lucide-x" @click="isAlertsOpen = false" />
          </div>
          
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <div v-if="lowStockItems.length === 0" class="text-center py-12">
              <UIcon name="i-lucide-check-circle-2" class="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p class="text-[var(--lh-ink-primary)] font-medium">All stock is healthy</p>
              <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">No containers are below their reorder points.</p>
            </div>
            
            <div v-for="item in lowStockItems" :key="item.id" class="lh-card border border-red-100 dark:border-red-900/30 bg-red-50/50 dark:bg-red-900/10">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="font-medium text-[var(--lh-ink-primary)]">{{ item.label }}</h3>
                  <p class="text-xs text-[var(--lh-ink-secondary)] mt-1">Reorder Point: {{ item.reorder_point }}</p>
                </div>
                <div class="text-right">
                  <span class="text-lg font-bold text-[var(--lh-danger)]">{{ item.current_stock }}</span>
                  <p class="text-xs text-[var(--lh-ink-secondary)]">Remaining</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </USlideover>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useWorkspace } from '../composables/useWorkspace'
import { useAlerts } from '../composables/useAlerts'

const { currentWorkspace } = useWorkspace()
const { lowStockItems, fetchAlerts } = useAlerts()

const isAlertsOpen = ref(false)

// Re-fetch alerts whenever the workspace changes or page loads
onMounted(() => {
  fetchAlerts()
})

watch(() => currentWorkspace.value, () => {
  fetchAlerts()
})
</script>
