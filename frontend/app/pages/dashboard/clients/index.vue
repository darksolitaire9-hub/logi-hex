<template>
  <div class="space-y-6 pb-20">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)]">Client Ledger</h1>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Manage clients and track their outstanding container balances.</p>
      </div>

      <div class="flex items-center space-x-3 w-full md:w-auto">
        <div class="relative flex-1 md:w-64">
          <UIcon name="i-lucide-search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Search clients..." 
            class="lh-input pl-9 w-full"
          />
        </div>
        <button @click="isAddModalOpen = true" class="lh-btn lh-btn-primary whitespace-nowrap">
          <UIcon name="i-lucide-user-plus" class="w-4 h-4 md:mr-2" />
          <span class="hidden md:inline">Add Client</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && clients.length === 0" class="flex justify-center py-12">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-[var(--lh-brand)] animate-spin" />
    </div>

    <!-- Empty State -->
    <div v-else-if="clients.length === 0" class="lh-card text-center py-12">
      <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
        <UIcon name="i-lucide-users" class="w-8 h-8 text-gray-400" />
      </div>
      <h3 class="text-lg font-medium text-[var(--lh-ink-primary)]">No clients yet</h3>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1 mb-6">Add your first client to start sending items out.</p>
      <button @click="isAddModalOpen = true" class="lh-btn lh-btn-primary mx-auto">
        Create First Client
      </button>
    </div>

    <!-- No Search Results -->
    <div v-else-if="filteredClients.length === 0" class="lh-card text-center py-12">
      <h3 class="text-lg font-medium text-[var(--lh-ink-primary)]">No clients match your search</h3>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Try a different name.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <NuxtLink 
        v-for="client in filteredClients" 
        :key="client.id" 
        :to="!client.deleted_at ? `/dashboard/clients/${client.id}` : '#'"
        :class="[
          'lh-card lh-card-interactive flex flex-col justify-between transition-colors',
          client.deleted_at ? 'opacity-60 bg-gray-50 dark:bg-gray-900/50 grayscale cursor-not-allowed pointer-events-none' : ''
        ]"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center">
            <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mr-3">
              <span class="text-[var(--lh-brand)] font-semibold text-sm">{{ client.name.substring(0, 2).toUpperCase() }}</span>
            </div>
            <h3 class="font-medium text-[var(--lh-ink-primary)] flex items-center">
              {{ client.name }}
              <span v-if="client.deleted_at" class="ml-2 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400">Archived</span>
            </h3>
          </div>
        </div>
        
        <div class="mt-6 pt-4 border-t border-[var(--lh-border-subtle)] flex items-center justify-between">
          <span class="text-sm text-[var(--lh-ink-secondary)]">Outstanding</span>
          <span :class="[
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
            (client.total_items_held || 0) > 0 
              ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300' 
              : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
          ]">
            {{ client.total_items_held || 0 }} items
          </span>
        </div>
      </NuxtLink>
    </div>

    <!-- Add Client Modal -->
    <UModal v-model="isAddModalOpen">
      <div class="p-6 bg-[var(--lh-bg-surface)] rounded-2xl border border-[var(--lh-border)] shadow-xl">
        <h3 class="text-lg font-semibold text-[var(--lh-ink-primary)] mb-4">Add New Client</h3>
        <form @submit.prevent="submitAdd" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Company / Client Name</label>
            <input 
              v-model="newClientForm.name" 
              type="text" 
              required 
              placeholder="e.g., Acme Corp" 
              class="lh-input"
              ref="nameInput"
            />
          </div>
          <div class="flex justify-end space-x-3 pt-4">
            <button type="button" @click="isAddModalOpen = false" class="lh-btn lh-btn-secondary">Cancel</button>
            <button type="submit" class="lh-btn lh-btn-primary" :disabled="!newClientForm.name">Create Client</button>
          </div>
        </form>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useClients } from '../../../composables/useClients'

definePageMeta({
  layout: 'default'
})

const { clients, loading, fetchClients, createClient } = useClients()

const isAddModalOpen = ref(false)
const newClientForm = ref({ name: '' })
const nameInput = ref<HTMLInputElement | null>(null)

const searchQuery = ref('')

const filteredClients = computed(() => {
  if (!searchQuery.value) return clients.value
  const q = searchQuery.value.toLowerCase()
  return clients.value.filter(c => c.name.toLowerCase().includes(q))
})

onMounted(async () => {
  await fetchClients()
})

// Watch for modal open to focus input
watch(isAddModalOpen, (val) => {
  if (val) {
    nextTick(() => {
      nameInput.value?.focus()
    })
  }
})

async function submitAdd() {
  if (!newClientForm.value.name) return
  const newId = await createClient(newClientForm.value.name, '')
  newClientForm.value = { name: '' }
  isAddModalOpen.value = false
}
</script>
