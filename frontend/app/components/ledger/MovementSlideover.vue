<template>
  <MovementForm
    v-model="isOpen"
    :client-id="clientId"
    :client-name="clientName"
    :is-sending="isSending"
    :force-direction="forceDirection"
    :pre-select-item="preSelectItem"
    :items="items"
    :items-loading="itemsLoading"
    :is-submitting="isSubmitting"
    @submit="handleLogMovement"
  />
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useItems } from '../../composables/useItems'
import { useLedger } from '../../composables/useLedger'
import { useSelfHealingUI } from '../../utils/errorDomains'
import MovementForm from './MovementForm.vue'

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
const { t } = useI18n()

// Watch for modal open to fetch items if catalog is empty
watch(() => props.modelValue, async (val) => {
  if (val && items.value.length === 0) {
    await fetchItems()
  }
})

async function handleLogMovement(payload: any) {
  try {
    await logMovement(payload)
    ui.handleUXSuccess('Movement Logged', t('movementSlideover.successMsg'))
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
