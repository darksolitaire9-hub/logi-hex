<template>
  <USlideover v-model="isOpen">
    <div class="flex flex-col h-full bg-[var(--lh-bg-surface)]">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-[var(--lh-border-subtle)] flex items-center justify-between bg-gray-50 dark:bg-gray-900/50">
        <div>
          <h2 class="text-lg font-semibold text-[var(--lh-ink-primary)]">
            {{ isSending ? 'Send Items Out' : 'Log Return / Collection' }}
          </h2>
          <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">
            {{ clientName }}
          </p>
        </div>
        <UButton color="neutral" variant="ghost" icon="i-lucide-x" @click="isOpen = false" />
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto px-6 py-5">
        <form @submit.prevent="handleSubmit" id="movementForm" class="space-y-6">
          
          <div v-if="itemsLoading" class="flex justify-center py-8">
            <UIcon name="i-lucide-loader-2" class="animate-spin text-[var(--lh-brand)] w-6 h-6" />
          </div>
          
          <div v-else-if="items.length === 0" class="text-center py-8 text-[var(--lh-ink-secondary)]">
            <p>No items defined in the catalog.</p>
            <NuxtLink to="/dashboard/items" class="text-[var(--lh-brand)] hover:underline text-sm block mt-2">Go to Item Catalog</NuxtLink>
          </div>

          <div v-else>
            <div class="space-y-4">
              <div v-for="item in items" :key="item.id" class="flex items-center justify-between p-3 rounded-lg border border-[var(--lh-border-subtle)] hover:border-gray-300 transition-colors">
                <div>
                  <div class="font-medium text-[var(--lh-ink-primary)]">{{ item.label }}</div>
                  <div class="text-xs text-[var(--lh-ink-secondary)]">{{ item.unit }}</div>
                </div>
                <div class="w-24">
                  <input 
                    type="number" 
                    min="0"
                    step="0.01"
                    placeholder="0"
                    v-model.number="quantities[item.id]"
                    class="lh-input text-right !h-10"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Notes / Exceptions for Collections -->
          <div v-if="!isSending">
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Exception / Reason</label>
            <select v-model="correctionReason" class="lh-input mb-3 text-sm">
              <option value="">Normal Return</option>
              <option value="DAMAGE">Damaged / Broken</option>
              <option value="LOSS">Lost by Client</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">Optional Notes</label>
            <textarea 
              v-model="notes" 
              class="lh-input !h-20 py-2 resize-none text-sm" 
              placeholder="Any details to attach to this movement..."
            ></textarea>
          </div>

        </form>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-[var(--lh-border-subtle)] bg-gray-50 dark:bg-gray-900/50 flex justify-end space-x-3">
        <button type="button" @click="isOpen = false" class="lh-btn lh-btn-secondary">Cancel</button>
        <button 
          type="submit" 
          form="movementForm" 
          class="lh-btn lh-btn-primary"
          :disabled="isSubmitting || !hasQuantities"
        >
          <UIcon v-if="isSubmitting" name="i-lucide-loader-2" class="w-4 h-4 mr-2 animate-spin" />
          {{ isSubmitting ? 'Logging...' : 'Confirm Logging' }}
        </button>
      </div>
    </div>
  </USlideover>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useItems } from '../../composables/useItems'
import { useLedger } from '../../composables/useLedger'
import { useSelfHealingUI } from '../../utils/errorDomains'
import type { CorrectionReason } from '../../types/domain'

const props = defineProps<{
  modelValue: boolean
  clientId: string
  clientName: string
  isSending: boolean
  forceDirection?: 'RECEIVE' | 'USE'
  preSelectItem?: string
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const { items, loading: itemsLoading, fetchItems } = useItems()
const { logMovement, loading: isSubmitting } = useLedger()
const ui = useSelfHealingUI()

// State
const quantities = ref<Record<string, number>>({})
const notes = ref('')
const correctionReason = ref<CorrectionReason | ''>('')

// Watch for modal open to reset state and fetch items
watch(() => props.modelValue, async (val) => {
  if (val) {
    quantities.value = {}
    notes.value = ''
    correctionReason.value = ''
    if (items.value.length === 0) {
      await fetchItems()
    }
  }
})

const hasQuantities = computed(() => {
  return Object.values(quantities.value).some(q => typeof q === 'number' && q > 0)
})

async function handleSubmit() {
  if (!hasQuantities.value) {
    ui.handleUXError('VALIDATION', 'Please enter a valid quantity.')
    return
  }

  // Build the lines array filtering out 0s
  const lines = Object.entries(quantities.value)
    .filter(([_, qty]) => typeof qty === 'number' && qty > 0)
    .map(([item_id, quantity]) => ({ item_id, quantity }))

  try {
    const finalDirection = props.forceDirection 
      ? props.forceDirection 
      : (props.isSending ? 'SEND' : 'COLLECT')

    await logMovement({
      direction: finalDirection,
      client_id: props.clientId || undefined,
      notes: notes.value || undefined,
      correction_reason: (props.isSending ? undefined : correctionReason.value) || undefined,
      lines
    })

    ui.handleUXSuccess('Movement Logged', `Successfully logged transaction.`)
    isOpen.value = false
    emit('success')
  } catch (e: any) {
    if (e.message?.toLowerCase().includes('database is locked')) {
      ui.handleUXError('DATABASE_LOCKED')
    } else {
      ui.handleUXError('UNKNOWN')
      console.error(e)
    }
  }
}
</script>
