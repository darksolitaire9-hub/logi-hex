<template>
  <div class="lh-card shadow-xl border-gray-200 dark:border-gray-800">
    <div class="text-center mb-6">
      <h2 class="text-xl font-semibold text-[var(--lh-ink-primary)]">{{ $t('onboarding.title') }}</h2>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">{{ $t('onboarding.subtitle') }}</p>
    </div>

    <form @submit.prevent="handleCreate" class="space-y-4">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('onboarding.fields.name.label') }}</label>
          <input 
            v-model="form.name"
            type="text" 
            required
            :placeholder="$t('onboarding.fields.name.placeholder')" 
            class="lh-input"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('onboarding.fields.timezone.label') }}</label>
          <select 
            v-model="form.timezone"
            required
            class="lh-input"
          >
            <option v-for="tz in availableTimezones" :key="tz" :value="tz">{{ tz }}</option>
          </select>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-2">{{ $t('onboarding.fields.mode.label') }}</label>
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
            <div class="font-medium text-sm text-[var(--lh-ink-primary)]">{{ $t('onboarding.modes.accounts.title') }}</div>
            <div class="text-xs text-[var(--lh-ink-secondary)] mt-1">{{ $t('onboarding.modes.accounts.desc') }}</div>
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
            <div class="font-medium text-sm text-[var(--lh-ink-primary)]">{{ $t('onboarding.modes.inventory.title') }}</div>
            <div class="text-xs text-[var(--lh-ink-secondary)] mt-1">{{ $t('onboarding.modes.inventory.desc') }}</div>
          </button>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('onboarding.fields.userPin.label') }}</label>
          <input 
            v-model="form.pin"
            type="password" 
            :placeholder="$t('onboarding.fields.userPin.placeholder')" 
            class="lh-input"
            required
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('onboarding.fields.adminPin.label') }}</label>
          <input 
            v-model="form.adminPin"
            type="password" 
            :placeholder="$t('onboarding.fields.adminPin.placeholder')" 
            class="lh-input"
            required
          />
        </div>
      </div>

      <div class="pt-4">
        <button 
          type="submit" 
          class="lh-btn lh-btn-primary w-full"
          :disabled="loading || !form.name || !form.pin || !form.adminPin"
        >
          <UIcon v-if="loading" name="i-lucide-loader-2" class="w-5 h-5 mr-2 animate-spin" />
          {{ loading ? $t('onboarding.buttons.creating') : $t('onboarding.buttons.create') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useWorkspace } from '../composables/useWorkspace'
import type { WorkspaceMode } from '../types/domain'

definePageMeta({
  layout: 'auth'
})

const router = useRouter()
const { t } = useI18n()
const { createWorkspace, fetchWorkspaces } = useWorkspace()

const loading = ref(false)
const availableTimezones = ref<string[]>([])
const form = ref({
  name: '',
  mode: 'INVENTORY' as WorkspaceMode,
  pin: '',
  adminPin: '',
  timezone: ''
})

onMounted(() => {
  try {
    availableTimezones.value = Intl.supportedValuesOf('timeZone')
    form.value.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch (e) {
    // Fallback if supportedValuesOf is not supported
    availableTimezones.value = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']
    form.value.timezone = 'UTC'
  }
})

async function handleCreate() {
  if (!form.value.name || !form.value.pin || !form.value.adminPin) return
  
  loading.value = true
  try {
    const success = await createWorkspace(
      form.value.name, 
      form.value.mode, 
      form.value.pin,
      form.value.adminPin,
      form.value.timezone
    )
    
    if (success) {
      await fetchWorkspaces()
      router.push('/')
    } else {
      alert(t('onboarding.errors.failed'))
    }
  } catch (e) {
    console.error(e)
    alert(t('onboarding.errors.failed'))
  } finally {
    loading.value = false
  }
}
</script>
