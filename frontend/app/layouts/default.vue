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
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Topbar for mobile -->
      <header class="md:hidden h-16 border-b border-[var(--lh-border-subtle)] bg-[var(--lh-bg-surface)] flex items-center justify-between px-4">
        <span class="font-semibold text-[var(--lh-ink-primary)]">Logi-Hex</span>
        <UButton icon="i-lucide-menu" color="gray" variant="ghost" />
      </header>
      
      <!-- Page View -->
      <div class="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
        <div class="max-w-7xl mx-auto">
          <slot />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useWorkspace } from '../composables/useWorkspace'

const { currentWorkspace } = useWorkspace()
</script>
