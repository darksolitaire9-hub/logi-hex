<template>
  <ForecastSettingsForm
    v-model="isOpen"
    :item="item"
    :loading-scores="loadingScores"
    :is-running-backtest="isRunningBacktest"
    :scores="scores"
    :best-engine="bestEngine"
    :override-selection="overrideSelection"
    @run-backtest="handleRunBacktest"
    @change-override="handleChangeOverride"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useForecasting, type EngineScore } from '../../../composables/useForecasting'
import type { Item } from '../../../types/domain'
import ForecastSettingsForm from './ForecastSettingsForm.vue'

const props = defineProps<{
  modelValue: boolean
  item: Item | null
}>()

const emit = defineEmits(['update:modelValue'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const { triggerBacktest, getScores, getBestEngine, getSettings, setUserOverride } = useForecasting()

const loadingScores = ref(false)
const isRunningBacktest = ref(false)
const scores = ref<EngineScore[]>([])
const bestEngine = ref<string>('Baseline_LastKnown')
const overrideSelection = ref('auto')

async function loadData() {
  if (!props.item) return
  loadingScores.value = true
  
  try {
    // 1. Fetch past scores for 14-day horizon
    scores.value = await getScores(props.item.id, 14)
    
    // 2. Fetch lock settings directly
    const settings = await getSettings(props.item.id)
    if (settings && settings.is_locked && settings.locked_engine_name) {
      overrideSelection.value = settings.locked_engine_name
    } else {
      overrideSelection.value = 'auto'
    }

    // 3. Resolve Best Engine (incorporating locks)
    bestEngine.value = await getBestEngine(props.item.id, 14)
  } catch (e) {
    console.error("Failed to load settings data:", e)
  } finally {
    loadingScores.value = false
  }
}

async function handleRunBacktest() {
  if (!props.item) return
  isRunningBacktest.value = true
  
  try {
    scores.value = await triggerBacktest(props.item.id, 14)
    bestEngine.value = await getBestEngine(props.item.id, 14)
  } catch (e) {
    console.error("Backtest failed:", e)
  } finally {
    isRunningBacktest.value = false
  }
}

async function handleChangeOverride(engine: string) {
  if (!props.item) return
  overrideSelection.value = engine
  
  const engineToLock = engine === 'auto' ? null : engine
  await setUserOverride(props.item.id, engineToLock, engine !== 'auto')
  
  // Re-evaluate best engine
  bestEngine.value = await getBestEngine(props.item.id, 14)
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadData()
  }
})
</script>
