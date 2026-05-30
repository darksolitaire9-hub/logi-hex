<template>
  <div>
    <div class="mb-8">
      <h1 class="text-2xl font-semibold text-[var(--lh-ink-primary)] flex items-center">
        <UIcon name="i-lucide-brain-circuit" class="w-6 h-6 mr-3 text-[var(--lh-brand)]" />
        Hybrid Forecasting Hub
      </h1>
      <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">
        Leverage statistical models and Google's TimesFM to predict inventory demand.
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
            <input type="range" v-model.number="horizon" min="7" max="90" step="1" class="w-full" :disabled="isForecasting || isLocked" />
            <span class="text-sm font-medium text-[var(--lh-ink-primary)] w-16 text-right">{{ horizon }} days</span>
          </div>
        </div>

        <div>
          <h2 class="text-sm font-medium text-[var(--lh-ink-secondary)] mb-3 uppercase tracking-wider">Human Override (Covariates)</h2>
          <p class="text-xs text-[var(--lh-ink-secondary)] mb-2">Adjust baseline math for unprecedented events (e.g., upcoming holidays).</p>
          <div class="flex items-center space-x-3">
            <input type="range" v-model.number="humanOverride" min="-100" max="200" step="5" class="w-full" :disabled="isForecasting || isLocked" />
            <span class="text-sm font-medium text-[var(--lh-ink-primary)] w-16 text-right">{{ humanOverride > 0 ? '+' : '' }}{{ humanOverride }}%</span>
          </div>
        </div>

        <div class="pt-4 border-t border-[var(--lh-border-subtle)]">
          <button 
            @click="runForecast" 
            :disabled="!selectedItemId || isForecasting || isLocked"
            class="lh-btn lh-btn-primary w-full justify-center"
          >
            <UIcon v-if="isForecasting" name="i-lucide-loader-2" class="w-4 h-4 mr-2 animate-spin" />
            <UIcon v-else-if="isLocked" name="i-lucide-lock" class="w-4 h-4 mr-2" />
            <UIcon v-else name="i-lucide-zap" class="w-4 h-4 mr-2" />
            {{ isForecasting ? 'Running AI Engine...' : (isLocked ? 'Not Enough Data' : 'Generate Forecast') }}
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
        
        <div v-if="!selectedItemId" class="flex-1 flex flex-col items-center justify-center text-center opacity-50">
          <UIcon name="i-lucide-line-chart" class="w-16 h-16 text-[var(--lh-ink-secondary)] mb-4" />
          <p class="text-sm text-[var(--lh-ink-primary)] font-medium">Select an Item</p>
          <p class="text-xs text-[var(--lh-ink-secondary)] mt-1">Choose an inventory item to analyze its future demand.</p>
        </div>

        <div v-else-if="isLocked" class="flex-1 flex flex-col items-center justify-center text-center px-6">
          <div class="bg-amber-100 dark:bg-amber-900/30 p-6 rounded-2xl flex flex-col items-center max-w-sm">
            <UIcon name="i-lucide-lock" class="w-12 h-12 text-amber-500 mb-4" />
            <p class="text-lg font-bold text-amber-800 dark:text-amber-400 mb-2">Forecasting Locked</p>
            <p class="text-sm text-amber-700 dark:text-amber-500 font-medium">
              The AI needs to learn your habits! Log outbound usage on at least 1 more day to unlock the prediction engine.
            </p>
          </div>
        </div>

        <div v-else-if="isForecasting" class="flex-1 flex flex-col items-center justify-center text-center px-6">
          <UIcon name="i-lucide-brain-circuit" class="w-12 h-12 text-[var(--lh-brand)] animate-pulse mb-4" />
          <p class="text-sm font-medium text-[var(--lh-ink-primary)]">Evaluating Historical Trajectory...</p>
          <p class="text-xs text-[var(--lh-ink-secondary)] mt-2 max-w-md">
            The hybrid sidecar is selecting the best mathematical model based on your data maturity.
          </p>
        </div>

        <div v-else-if="!forecastResult" class="flex-1 flex flex-col items-center justify-center text-center opacity-50">
          <UIcon name="i-lucide-check-circle" class="w-16 h-16 text-green-500 mb-4" />
          <p class="text-sm text-[var(--lh-ink-primary)] font-medium">Ready to Forecast</p>
          <p class="text-xs text-[var(--lh-ink-secondary)] mt-1">We have enough data ({{ cachedHistoryLength }} days). Click Generate Forecast.</p>
        </div>

        <div v-else class="flex-1 flex flex-col">
          <!-- Temporary simple visualization without heavy chart libs -->
          <div class="flex-1 flex items-end space-x-1 px-4 pb-8 pt-4">
            <div 
              v-for="(val, idx) in forecastResult" 
              :key="idx"
              class="flex-1 rounded-t transition-all relative group"
              :class="humanDelta !== 0 ? 'bg-purple-300 dark:bg-purple-700/50 hover:bg-purple-400' : 'bg-blue-200 dark:bg-blue-800/50 hover:bg-blue-400'"
              :style="{ height: `${Math.min(100, Math.max(5, (val / maxForecastValue) * 100))}%` }"
            >
              <div class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10 pointer-events-none">
                Day +{{ idx + 1 }}: {{ val.toFixed(1) }}
              </div>
            </div>
          </div>
          
          <div class="flex justify-between items-center text-xs text-[var(--lh-ink-secondary)] border-t border-[var(--lh-border-subtle)] pt-3">
            <span>Tomorrow</span>
            <div class="flex flex-col items-center">
              <span class="font-medium bg-[var(--lh-bg-elevated)] px-2 py-1 rounded-md mb-1">Engine: {{ modelUsed }}</span>
              <button @click="isKnowledgeDrawerOpen = true" class="text-blue-500 hover:text-blue-600 dark:text-blue-400 flex items-center text-[10px] uppercase font-bold tracking-wider">
                <UIcon name="i-lucide-book-open" class="w-3 h-3 mr-1" />
                How was this calculated?
              </button>
            </div>
            <span>+{{ horizon }} Days</span>
          </div>
          
          <div class="flex justify-between text-xs text-[var(--lh-ink-secondary)] border-t border-[var(--lh-border-subtle)] pt-3">
            <span>Tomorrow</span>
            <span>+{{ horizon }} Days</span>
          </div>
        </div>
      </div>
    </div>

    <!-- JIT Learning: Knowledge Drawer -->
    <USlideover v-model="isKnowledgeDrawerOpen" side="right">
      <div class="p-6 h-full flex flex-col bg-white dark:bg-gray-900">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-lg font-bold text-[var(--lh-ink-primary)] flex items-center">
            <UIcon name="i-lucide-graduation-cap" class="w-5 h-5 mr-2 text-[var(--lh-brand)]" />
            Forecasting Engine Logic
          </h2>
          <button @click="isKnowledgeDrawerOpen = false" class="text-gray-500 hover:text-gray-800 dark:hover:text-gray-300">
            <UIcon name="i-lucide-x" class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-6 flex-1 overflow-y-auto pr-2">
          
          <div v-if="modelUsed.includes('TimesFM')" class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
            <h3 class="font-bold text-blue-800 dark:text-blue-300 mb-2 flex items-center">
              <UIcon name="i-lucide-cpu" class="w-4 h-4 mr-2" />
              TimesFM 1.0 (Google AI)
            </h3>
            <p class="text-sm text-blue-900/80 dark:text-blue-200/80 mb-3 leading-relaxed">
              Because you have logged more than 14 days of data, the system successfully triggered the TimesFM Deep Learning model.
            </p>
            <div class="text-xs bg-white dark:bg-gray-800 p-3 rounded-lg border border-blue-100 dark:border-blue-700/50 font-mono">
              Formula: AI Zero-Shot Autoregressive Prediction over 200M parameters.
            </div>
          </div>

          <div v-else class="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl border border-emerald-200 dark:border-emerald-800">
            <h3 class="font-bold text-emerald-800 dark:text-emerald-300 mb-2 flex items-center">
              <UIcon name="i-lucide-sigma" class="w-4 h-4 mr-2" />
              Statistical Fallback Math
            </h3>
            <p class="text-sm text-emerald-900/80 dark:text-emerald-200/80 mb-3 leading-relaxed">
              Because you have logged less than 14 days of data, the AI has deferred to traditional enterprise statistics (Negative Space Programming).
            </p>
            <div class="text-xs bg-white dark:bg-gray-800 p-3 rounded-lg border border-emerald-100 dark:border-emerald-700/50 font-mono">
              Formula: {{ modelUsed === 'MathFallback:HistoricAverage' ? 'Mean(All Historical Points)' : 'Last 7 Days Repeated' }}
            </div>
          </div>

          <div class="pt-6 border-t border-gray-200 dark:border-gray-800">
            <h3 class="font-bold text-[var(--lh-ink-primary)] mb-2">Company Override Policy</h3>
            <p class="text-sm text-[var(--lh-ink-secondary)] leading-relaxed">
              You are permitted to use the <strong>Unit Adjustment Delta</strong> to override the mathematical baseline. 
            </p>
            <div class="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg flex">
              <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 text-amber-500 mr-2 flex-shrink-0 mt-0.5" />
              <p class="text-xs text-amber-800 dark:text-amber-400">
                <strong>Auditing Standard:</strong> Any deterministic adjustment must be accompanied by a clear Reason text. This data is permanently logged in the <code>forecast_audit_logs</code> table.
              </p>
            </div>
          </div>

        </div>
      </div>
    </USlideover>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
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
const { getItemMovementHistory, saveForecastAudit } = useLedger()

const selectedItemId = ref('')
const horizon = ref(30)
const humanDelta = ref(0)
const overrideReason = ref('')
const isForecasting = ref(false)
const forecastResult = ref<number[] | null>(null)
const error = ref<string | null>(null)
const cachedHistoryLength = ref(0)
const cachedHistorySnapshot = ref<number[]>([])
const modelUsed = ref('')

const isKnowledgeDrawerOpen = ref(false)

const isLocked = computed(() => !!selectedItemId.value && cachedHistoryLength.value < 1)

watch(selectedItemId, async (newId) => {
  if (newId) {
    const history = await getItemMovementHistory(newId)
    cachedHistoryLength.value = history.length
    cachedHistorySnapshot.value = history
    forecastResult.value = null
  }
})

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
    // 1. DATA GRAVITY: Rust backend will fetch history directly from SQLite
    const responseJson = await invoke<string>('run_ml_forecast', {
      itemId: selectedItemId.value,
      horizon: horizon.value
    })
    
    let baseForecast;
    try {
      baseForecast = JSON.parse(responseJson)
    } catch (parseErr) {
      throw new Error(`Invalid forecast response: ${responseJson}`);
    }
    
    if (Array.isArray(baseForecast)) {
      modelUsed.value = 'Local TimesFM (Rust/ONNX)'
      
      // Calculate total base prediction
      const totalBase = baseForecast.reduce((sum: number, v: number) => sum + v, 0)
      
      // Apply Deterministic Human Override (Delta added linearly across the horizon)
      const dailyDelta = humanDelta.value / horizon.value
      const adjustedForecast = baseForecast.map((v: number) => Math.max(0, v + dailyDelta))
      forecastResult.value = adjustedForecast
      
      // Calculate total final prediction
      const totalFinal = adjustedForecast.reduce((sum: number, v: number) => sum + v, 0)
      
      // AUDIT LOG: Save Provenance
      await saveForecastAudit({
        item_id: selectedItemId.value,
        model_used: modelUsed.value,
        input_snapshot: JSON.stringify(cachedHistorySnapshot.value),
        base_prediction: totalBase,
        human_override_percentage: 0, // Deprecated percentage
        human_adjustment_qty: humanDelta.value,
        override_reason: overrideReason.value,
        final_prediction: totalFinal
      })
      
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
