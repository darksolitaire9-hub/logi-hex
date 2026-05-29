<template>
  <div class="lh-card shadow-xl border-gray-200 dark:border-gray-800">
    <div class="text-center mb-6">
      <h2 class="text-xl font-semibold text-[var(--lh-ink-primary)]">Create Workspace</h2>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Set up your first command center</p>
    </div>

    <form @submit.prevent="handleCreate" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Workspace Name</label>
        <input 
          v-model="form.name"
          type="text" 
          required
          placeholder="e.g., Main Warehouse" 
          class="lh-input"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-2">Operating Mode</label>
        <div class="grid grid-cols-2 gap-3">
          <!-- Accounts Mode -->
          <button 
            type="button"
            @click="form.mode = 'ACCOUNTS'"
            :class="[
              'p-4 rounded-xl border text-left transition-all',
              form.mode === 'ACCOUNTS' 
                ? 'border-[var(--lh-brand)] bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-500/20' 
                : 'border-[var(--lh-border)] bg-[var(--lh-bg-surface)] hover:border-gray-400'
            ]"
          >
            <UIcon name="i-lucide-users" :class="['w-6 h-6 mb-2', form.mode === 'ACCOUNTS' ? 'text-[var(--lh-brand)]' : 'text-gray-400']" />
            <div class="font-medium text-sm text-[var(--lh-ink-primary)]">Accounts</div>
            <div class="text-xs text-[var(--lh-ink-secondary)] mt-1">Blind ledger tracking</div>
          </button>

          <!-- Inventory Mode -->
          <button 
            type="button"
            @click="form.mode = 'INVENTORY'"
            :class="[
              'p-4 rounded-xl border text-left transition-all',
              form.mode === 'INVENTORY' 
                ? 'border-[var(--lh-brand)] bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-500/20' 
                : 'border-[var(--lh-border)] bg-[var(--lh-bg-surface)] hover:border-gray-400'
            ]"
          >
            <UIcon name="i-lucide-package" :class="['w-6 h-6 mb-2', form.mode === 'INVENTORY' ? 'text-[var(--lh-brand)]' : 'text-gray-400']" />
            <div class="font-medium text-sm text-[var(--lh-ink-primary)]">Inventory</div>
            <div class="text-xs text-[var(--lh-ink-secondary)] mt-1">Stock and forecasts</div>
          </button>
        </div>
      </div>

      <div class="pt-2">
        <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Security PIN (Optional)</label>
        <p class="text-xs text-[var(--lh-ink-secondary)] mb-2">Lock this workspace to prevent unauthorized access on this device.</p>
        <input 
          v-model="form.pin"
          type="password" 
          placeholder="Enter a 4-6 digit PIN" 
          class="lh-input"
        />
      </div>

      <div class="pt-4">
        <button 
          type="submit" 
          class="lh-btn lh-btn-primary w-full"
          :disabled="loading || !form.name"
        >
          <UIcon v-if="loading" name="i-lucide-loader-2" class="w-5 h-5 mr-2 animate-spin" />
          {{ loading ? 'Creating...' : 'Create Workspace' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspace } from '../composables/useWorkspace'
import type { WorkspaceMode } from '../types/domain'

definePageMeta({
  layout: 'auth'
})

const router = useRouter()
const { createWorkspace, fetchWorkspaces } = useWorkspace()

const loading = ref(false)
const form = ref({
  name: '',
  mode: 'INVENTORY' as WorkspaceMode,
  pin: ''
})

// Simple hash implementation for the PIN so we don't store plain text
// In a production app you'd use a crypto library, but we just need a local lock
async function hashPin(pin: string): Promise<string> {
  const msgUint8 = new TextEncoder().encode(pin)
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

async function handleCreate() {
  if (!form.value.name) return
  
  loading.value = true
  try {
    let pinHash = null
    if (form.value.pin) {
      pinHash = await hashPin(form.value.pin)
    }

    await createWorkspace({
      name: form.value.name,
      mode: form.value.mode,
      password_hash: pinHash
    })

    // Immediately fetch and redirect to the gatekeeper (index)
    await fetchWorkspaces()
    router.push('/')
  } catch (e) {
    console.error(e)
    alert('Failed to create workspace')
  } finally {
    loading.value = false
  }
}
</script>
