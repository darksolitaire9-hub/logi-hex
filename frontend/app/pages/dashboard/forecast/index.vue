<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)] flex items-center">
        <UIcon name="i-lucide-brain-circuit" class="w-6 h-6 mr-3 text-[var(--lh-brand)]" />
        TimesFM Forecasting Hub
      </h1>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">
        Leverage Google's TimesFM machine learning sidecar to predict future inventory usage.
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Sidecar Control Panel -->
      <div class="lh-card col-span-1 flex flex-col space-y-6">
        <div>
          <h2 class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-3 uppercase tracking-wider">Select Item</h2>
          <select v-model="selectedItemId" class="lh-input" :disabled="isForecasting">
            <option value="" disabled>Select an item to forecast...</option>
            <option v-for="item in items" :key="item.id" :value="item.id">
              {{ item.label }} (Current: {{ item.current_stock }})
            </option>
          </select>
        </div>

        <div>
          <h2 class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-3 uppercase tracking-wider">Prediction Horizon</h2>
          <div class="flex items-center space-x-3">
            <input type="range" v-model.number="horizon" min="7" max="90" step="1" class="w-full" :disabled="isForecasting" />
            <span class="text-sm font-medium text-[var(--lh-ink-primary)] w-16 text-right">{{ horizon }} days</span>
          </div>
        </div>

        <div class="pt-4 border-t border-[var(--lh-border-subtle)]">
          <button 
            @click="runForecast" 
            :disabled="!selectedItemId || isForecasting"
            class="lh-btn lh-btn-primary w-full justify-center"
          >
            <UIcon v-if="isForecasting" name="i-lucide-loader-2" class="w-4 h-4 mr-2 animate-spin" />
            <UIcon v-else name="i-lucide-zap" class="w-4 h-4 mr-2" />
            {{ isForecasting ? 'Sidecar Running...' : 'Spawn ML Sidecar' }}
          </button>
        </div>
        
        <div v-if="error" class="p-3 bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400 text-sm rounded-lg border border-red-200 dark:border-red-800">
          <div class="font-medium mb-1">Sidecar Error</div>
          <div>{{ error }}</div>
          <div class="mt-2 text-xs opacity-80">Did you bundle the PyInstaller binary? During local dev without it, the sidecar binary isn't found.</div>
        </div>
      </div>

      <!-- Graph Area -->
      <div class="lh-card col-span-1 lg:col-span-2 min-h-[400px] flex flex-col relative">
        <h2 class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-4 uppercase tracking-wider">Forecast Trajectory</h2>
        
        <div v-if="!forecastResult && !isForecasting" class="flex-1 flex flex-col items-center justify-center text-center opacity-50">
          <UIcon name="i-lucide-line-chart" class="w-16 h-16 text-[var(--lh-ink-secondary)] mb-4" />
          <p class="text-sm text-[var(--lh-ink-primary)] font-medium">No Forecast Rendered</p>
          <p class="text-xs text-[var(--lh-ink-secondary)] mt-1">Select an item and run the sidecar to generate predictions.</p>
        </div>

        <div v-else-if="isForecasting" class="flex-1 flex flex-col items-center justify-center text-center px-6">
          <UIcon name="i-lucide-brain-circuit" class="w-12 h-12 text-[var(--lh-brand)] animate-pulse mb-4" />
          <p class="text-sm font-medium text-[var(--lh-ink-primary)]">Running TimesFM Machine Learning Model...</p>
          <p class="text-xs text-[var(--lh-ink-secondary)] mt-2 max-w-md">
            Note: On the first run, the sidecar will download ~200MB of pre-trained model weights from HuggingFace. This can take 1–3 minutes depending on your internet connection. Subsequent runs will be instantaneous.
          </p>
        </div>

        <div v-else class="flex-1 flex flex-col">
          <!-- Temporary simple visualization without heavy chart libs -->
          <div class="flex-1 flex items-end space-x-1 px-4 pb-8 pt-4">
            <div 
              v-for="(val, idx) in forecastResult" 
              :key="idx"
              class="flex-1 bg-blue-200 dark:bg-blue-800/50 rounded-t transition-all hover:bg-blue-400 dark:hover:bg-blue-600 relative group"
              :style="{ height: `${Math.min(100, Math.max(5, (val / maxForecastValue) * 100))}%` }"
            >
              <div class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10 pointer-events-none">
                Day +{{ idx + 1 }}: {{ val.toFixed(1) }}
              </div>
            </div>
          </div>
          
          <div class="flex justify-between text-xs text-[var(--lh-ink-secondary)] border-t border-[var(--lh-border-subtle)] pt-3">
            <span>Tomorrow</span>
            <span>+{{ horizon }} Days</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { useItems } from '../../../composables/useItems'
import { useDatabase } from '../../../composables/useDatabase'
import { useWorkspace } from '../../../composables/useWorkspace'
import { useLedger } from '../../../composables/useLedger'

definePageMeta({
  layout: 'default'
})

const { currentWorkspace } = useWorkspace()
const { items, fetchItems } = useItems()
const { getItemMovementHistory } = useLedger()

const selectedItemId = ref('')
const horizon = ref(30)
const isForecasting = ref(false)
const forecastResult = ref<number[] | null>(null)
const error = ref<string | null>(null)

onMounted(async () => {
  await fetchItems()
})

const maxForecastValue = computed(() => {
  if (!forecastResult.value || forecastResult.value.length === 0) return 100
  return Math.max(...forecastResult.value, 10) // Minimum scale of 10
})

async function runForecast() {
  if (!selectedItemId.value || !currentWorkspace.value) return
  
  error.value = null
  isForecasting.value = true
  forecastResult.value = null
  
  try {
    const history = await getItemMovementHistory(selectedItemId.value)
    
    if (history.length === 0) {
      error.value = 'No movement history found for this item. Please log some movements (e.g. Receive, Send, Use) to generate a forecast.'
      return
    }
    
    // Invoke the Rust command, which spawns the Python sidecar
    const responseJson = await invoke<string>('run_ml_forecast', {
      history: JSON.stringify(history),
      horizon: horizon.value
    })
    
    const response = JSON.parse(responseJson)
    
    if (response.status === 'success') {
      forecastResult.value = response.forecast
    } else {
      error.value = response.message || 'Unknown error from Sidecar'
    }
  } catch (err: any) {
    console.error('Forecast error:', err)
    error.value = err.toString()
  } finally {
    isForecasting.value = false
  }
}
</script>
