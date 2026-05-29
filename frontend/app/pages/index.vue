<template>
  <div class="lh-card shadow-xl border-gray-200 dark:border-gray-800">
    <div class="text-center mb-6">
      <div v-if="!currentWorkspace">
        <h2 class="text-xl font-semibold text-[var(--lh-ink-primary)]">Select Workspace</h2>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">Choose a workspace to unlock</p>
      </div>
      <div v-else>
        <div class="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mx-auto mb-4">
          <UIcon :name="currentWorkspace.mode === 'ACCOUNTS' ? 'i-lucide-users' : 'i-lucide-package'" class="text-[var(--lh-brand)] w-8 h-8" />
        </div>
        <h2 class="text-xl font-semibold text-[var(--lh-ink-primary)]">{{ currentWorkspace.name }}</h2>
        <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">
          {{ currentWorkspace.mode === 'ACCOUNTS' ? 'Accounts Mode' : 'Inventory Mode' }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-8">
      <UIcon name="i-lucide-loader-2" class="w-8 h-8 text-[var(--lh-brand)] animate-spin" />
    </div>

    <div v-else-if="workspaces.length === 0" class="text-center py-4">
      <p class="text-sm text-[var(--lh-ink-secondary)] mb-4">No workspaces found.</p>
      <NuxtLink to="/onboarding" class="lh-btn lh-btn-primary w-full inline-flex">
        Create Workspace
      </NuxtLink>
    </div>

    <form v-else-if="currentWorkspace" @submit.prevent="handleUnlock" class="space-y-4">
      <div v-if="currentWorkspace.password_hash">
        <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Enter Security PIN</label>
        <input 
          v-model="pin"
          type="password" 
          ref="pinInput"
          placeholder="••••" 
          class="lh-input text-center tracking-widest text-lg"
          required
        />
        <p v-if="errorMsg" class="text-sm text-[var(--lh-danger)] mt-2 text-center">{{ errorMsg }}</p>
      </div>
      <div v-else class="py-2 text-center">
        <p class="text-sm text-[var(--lh-ink-secondary)]">This workspace is unlocked.</p>
      </div>

      <div class="pt-4 space-y-3">
        <button 
          type="submit" 
          class="lh-btn lh-btn-primary w-full"
        >
          <UIcon name="i-lucide-unlock" class="w-4 h-4 mr-2" />
          {{ currentWorkspace.password_hash ? 'Unlock' : 'Enter Workspace' }}
        </button>

        <button 
          v-if="workspaces.length > 1"
          type="button" 
          @click="clearCurrentWorkspace"
          class="lh-btn lh-btn-secondary w-full"
        >
          Switch Workspace
        </button>
      </div>
    </form>

    <div v-else class="space-y-2">
      <!-- Workspace Selection List -->
      <button 
        v-for="ws in workspaces" 
        :key="ws.id"
        @click="selectWorkspaceForUnlock(ws.id)"
        class="w-full flex items-center p-4 rounded-xl border border-[var(--lh-border-subtle)] bg-[var(--lh-bg-surface)] hover:border-[var(--lh-border)] transition-colors text-left"
      >
        <div class="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center mr-3">
          <UIcon :name="ws.mode === 'ACCOUNTS' ? 'i-lucide-users' : 'i-lucide-package'" class="text-gray-600 dark:text-gray-400 w-5 h-5" />
        </div>
        <div class="flex-1">
          <div class="font-medium text-[var(--lh-ink-primary)]">{{ ws.name }}</div>
          <div class="text-xs text-[var(--lh-ink-secondary)]">
            <UIcon v-if="ws.password_hash" name="i-lucide-lock" class="w-3 h-3 inline mr-1" />
            {{ ws.mode === 'ACCOUNTS' ? 'Accounts' : 'Inventory' }}
          </div>
        </div>
      </button>

      <div class="pt-4 border-t border-[var(--lh-border-subtle)] mt-4">
        <NuxtLink to="/onboarding" class="text-sm text-[var(--lh-brand)] hover:underline flex items-center justify-center">
          <UIcon name="i-lucide-plus" class="w-4 h-4 mr-1" />
          Create another workspace
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspace } from '../composables/useWorkspace'

definePageMeta({
  layout: 'auth'
})

const router = useRouter()
const { workspaces, currentWorkspace, loading, fetchWorkspaces, selectWorkspace } = useWorkspace()

const pin = ref('')
const errorMsg = ref('')
const pinInput = ref<HTMLInputElement | null>(null)

onMounted(async () => {
  await fetchWorkspaces()
  
  // If no workspaces exist, immediately redirect to onboarding
  if (workspaces.value.length === 0) {
    router.replace('/onboarding')
    return
  }

  // Restore last selected workspace
  const savedId = localStorage.getItem('lh_active_workspace')
  if (savedId) {
    const ws = workspaces.value.find(w => w.id === savedId)
    if (ws) {
      currentWorkspace.value = ws
      // Auto-focus the PIN input for frictionless entry
      nextTick(() => {
        pinInput.value?.focus()
      })
    }
  }
})

function selectWorkspaceForUnlock(id: string) {
  const ws = workspaces.value.find(w => w.id === id)
  if (ws) {
    currentWorkspace.value = ws
    errorMsg.value = ''
    pin.value = ''
    nextTick(() => {
      pinInput.value?.focus()
    })
  }
}

function clearCurrentWorkspace() {
  currentWorkspace.value = null
  errorMsg.value = ''
  pin.value = ''
}

async function hashPin(pinText: string): Promise<string> {
  const msgUint8 = new TextEncoder().encode(pinText)
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

async function handleUnlock() {
  if (!currentWorkspace.value) return

  errorMsg.value = ''

  if (currentWorkspace.value.password_hash) {
    const enteredHash = await hashPin(pin.value)
    if (enteredHash !== currentWorkspace.value.password_hash) {
      errorMsg.value = 'Incorrect PIN'
      pin.value = ''
      pinInput.value?.focus()
      return
    }
  }

  // Set as active in composable
  await selectWorkspace(currentWorkspace.value.id)
  
  // Navigate to main dashboard
  router.push('/dashboard')
}
</script>
