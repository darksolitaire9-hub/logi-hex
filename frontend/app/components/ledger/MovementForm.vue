<template>
  <USlideover v-model="isOpen">
    <div class="flex flex-col h-full bg-[var(--lh-bg-surface)]">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-[var(--lh-border-subtle)] flex items-center justify-between bg-gray-50 dark:bg-gray-900/50">
        <div>
          <h2 class="text-lg font-semibold text-[var(--lh-ink-primary)]">
            {{ isSending ? $t('movementSlideover.titleSend') : $t('movementSlideover.titleReceive') }}
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
            <p>{{ $t('movementSlideover.noItems') }}</p>
            <NuxtLink to="/dashboard/items" class="text-[var(--lh-brand)] hover:underline text-sm block mt-2">{{ $t('movementSlideover.goToCatalog') }}</NuxtLink>
          </div>

          <div v-else>
            <div class="space-y-4">
              <div v-for="item in items" :key="item.id" class="flex items-center justify-between p-3 rounded-lg border border-[var(--lh-border-subtle)] hover:border-gray-300 transition-colors">
                <div class="flex-1">
                  <div class="font-medium text-[var(--lh-ink-primary)]" :data-testid="`item-label-${item.id}`">{{ item.label }}</div>
                  <select 
                    v-if="item.uoms && item.uoms.length > 0" 
                    v-model="selectedUoms[item.id]" 
                    class="lh-input !h-7 !py-0 !text-xs mt-1 w-32"
                    :data-testid="`uom-select-${item.id}`"
                  >
                    <option v-for="u in item.uoms" :key="u.id" :value="u.id">{{ u.unit_name }} ({{ u.multiplier }}x)</option>
                  </select>
                  <div v-else class="text-xs text-[var(--lh-ink-secondary)] mt-1">{{ item.base_unit_name }}</div>
                </div>
                <div class="w-24">
                  <input 
                    type="number" 
                    min="0"
                    step="0.01"
                    placeholder="0"
                    v-model.number="quantities[item.id]"
                    class="lh-input text-right !h-10"
                    :data-testid="`qty-input-${item.id}`"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Notes / Exceptions for Collections -->
          <div v-if="!isSending">
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('movementSlideover.exceptionLabel') }}</label>
            <select v-model="correctionReason" data-testid="correction-reason" class="lh-input mb-3 text-sm">
              <option value="">{{ $t('movementSlideover.exceptionNormal') }}</option>
              <option value="DAMAGE">{{ $t('movementSlideover.exceptionDamage') }}</option>
              <option value="LOSS">{{ $t('movementSlideover.exceptionLoss') }}</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-[var(--lh-ink-primary)] mb-1">{{ $t('movementSlideover.notesLabel') }}</label>
            <textarea 
              v-model="notes" 
              data-testid="movement-notes"
              class="lh-input !h-20 py-2 resize-none text-sm" 
              :placeholder="$t('movementSlideover.notesPlaceholder')"
            ></textarea>
          </div>

        </form>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-[var(--lh-border-subtle)] bg-gray-50 dark:bg-gray-900/50 flex justify-end space-x-3">
        <button type="button" data-testid="cancel-movement-btn" @click="isOpen = false" class="lh-btn lh-btn-secondary">{{ $t('actions.cancel') }}</button>
        <button 
          type="submit" 
          form="movementForm" 
          data-testid="confirm-movement-btn"
          class="lh-btn lh-btn-primary"
          :disabled="isSubmitting || !hasQuantities"
        >
          <UIcon v-if="isSubmitting" name="i-lucide-loader-2" class="w-4 h-4 mr-2 animate-spin" />
          {{ isSubmitting ? $t('movementSlideover.loggingBtn') : $t('movementSlideover.confirmBtn') }}
        </button>
      </div>
    </div>
  </USlideover>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Item, CorrectionReason } from '../../types/domain'

const props = defineProps<{
  modelValue: boolean
  clientId: string
  clientName: string
  isSending: boolean
  forceDirection?: 'RECEIVE' | 'USE'
  preSelectItem?: string
  items: Item[]
  itemsLoading: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits(['update:modelValue', 'submit'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Local form state
const quantities = ref<Record<string, number>>({})
const selectedUoms = ref<Record<string, string>>({})
const notes = ref('')
const correctionReason = ref<CorrectionReason | ''>('')

// Reset state when slideover opens
watch(() => props.modelValue, (val) => {
  if (val) {
    quantities.value = {}
    selectedUoms.value = {}
    notes.value = ''
    correctionReason.value = ''
    
    // Set default UOMs
    for (const item of props.items) {
      if (item.uoms && item.uoms.length > 0) {
        selectedUoms.value[item.id] = item.primary_uom_id || item.uoms[0]?.id || ''
      }
    }
  }
})

// Keep default UOM selection updated if items load late
watch(() => props.items, (newItems) => {
  if (props.modelValue && newItems.length > 0) {
    for (const item of newItems) {
      if (!selectedUoms.value[item.id] && item.uoms && item.uoms.length > 0) {
        selectedUoms.value[item.id] = item.primary_uom_id || item.uoms[0]?.id || ''
      }
    }
  }
}, { deep: true })

const hasQuantities = computed(() => {
  return Object.values(quantities.value).some(q => typeof q === 'number' && q > 0)
})

function handleSubmit() {
  if (!hasQuantities.value) return

  // Build lines array filtering out 0s
  const lines = Object.entries(quantities.value)
    .filter(([_, qty]) => typeof qty === 'number' && qty > 0)
    .map(([item_id, quantity]) => {
      const item = props.items.find(i => i.id === item_id)
      let multiplier = 1.0
      let uomName = item?.base_unit_name || 'Pieces'
      
      const selUomId = selectedUoms.value[item_id]
      if (selUomId && item?.uoms) {
        const u = item.uoms.find(u => u.id === selUomId)
        if (u) {
          multiplier = u.multiplier
          uomName = u.unit_name
        }
      }

      return { 
        item_id, 
        quantity, 
        multiplier, 
        recorded_unit: uomName 
      }
    })

  const finalDirection = props.forceDirection 
    ? props.forceDirection 
    : (props.isSending ? 'SEND' : 'COLLECT')

  emit('submit', {
    direction: finalDirection,
    client_id: props.clientId || undefined,
    notes: notes.value || undefined,
    correction_reason: (props.isSending ? undefined : correctionReason.value) || undefined,
    lines
  })
}
</script>
