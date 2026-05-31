<template>
  <USlideover v-model="isOpen" :ui="{ width: 'w-full max-w-md' }">
    <div class="flex flex-col h-full bg-[var(--lh-bg-surface)] overflow-hidden">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-[var(--lh-border-subtle)] flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-[var(--lh-ink-primary)]">Forecast Settings</h2>
          <p class="text-sm text-[var(--lh-ink-secondary)] mt-1">
            Engine selection and backtest scoring for <span class="font-medium text-[var(--lh-brand)]">{{ item?.label }}</span>
          </p>
        </div>
        <button @click="isOpen = false" class="text-gray-400 hover:text-gray-500">
          <UIcon name="i-lucide-x" class="w-5 h-5" />
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-6 space-y-8">
        
        <!-- Orchestrator Summary (Explain) -->
        <div class="lh-card bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-900/30">
          <div class="flex items-start">
            <UIcon name="i-lucide-bot" class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3" />
            <div>
              <h3 class="text-sm font-semibold text-blue-900 dark:text-blue-300">Orchestrator Decision</h3>
              <p class="text-sm text-blue-800 dark:text-blue-400 mt-1">
                <span v-if="loadingScores">Analyzing historical demand...</span>
                <span v-else-if="scores.length === 0">No backtest history available. Please run a backtest to benchmark the AI engines.</span>
                <span v-else>
                  Currently using <strong class="font-bold">{{ selectedEngineDisplay }}</strong>. 
                  <span v-if="isLocked">This was manually forced by a user override.</span>
                  <span v-else>This engine was auto-selected because it had the lowest Mean Absolute Scaled Error (MASE) on holdout data.</span>
                </span>
              </p>
            </div>
          </div>
        </div>

        <!-- Backtest Trigger -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-[var(--lh-ink-primary)]">Latest Benchmarks (14-Day Horizon)</h3>
            <button 
              @click="$emit('run-backtest')" 
              :disabled="isRunningBacktest"
              class="lh-btn lh-btn-secondary !py-1 !text-xs"
            >
              <UIcon v-if="isRunningBacktest" name="i-lucide-loader-2" class="w-3 h-3 mr-1 animate-spin" />
              <UIcon v-else name="i-lucide-play" class="w-3 h-3 mr-1" />
              {{ isRunningBacktest ? 'Testing...' : 'Run Backtest' }}
            </button>
          </div>

          <div v-if="scores.length > 0" class="space-y-3">
            <div v-for="score in sortedScores" :key="score.engine_name" 
                 class="p-3 rounded-lg border border-[var(--lh-border-subtle)] bg-white dark:bg-gray-800 flex justify-between items-center relative overflow-hidden"
                 :class="{ 'ring-2 ring-[var(--lh-brand)]': score.engine_name === bestEngine && !isLocked }"
            >
              <div v-if="score.engine_name === bestEngine && !isLocked" class="absolute top-0 right-0 bg-[var(--lh-brand)] text-white text-[10px] px-2 py-0.5 font-bold rounded-bl-lg">WINNER</div>
              
              <div>
                <p class="text-sm font-semibold text-[var(--lh-ink-primary)]">{{ formatEngineName(score.engine_name) }}</p>
                <div class="flex items-center space-x-4 mt-1 text-xs text-[var(--lh-ink-secondary)]">
                  <span title="Weighted Absolute Percentage Error">
                    WAPE: {{ score.wape !== null ? (score.wape * 100).toFixed(1) + '%' : 'N/A' }}
                  </span>
                  <span title="Mean Absolute Scaled Error">
                    MASE: {{ score.mase !== null ? score.mase.toFixed(2) : 'N/A' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="!loadingScores" class="text-sm text-[var(--lh-ink-secondary)] italic text-center py-6 border border-dashed border-[var(--lh-border-subtle)] rounded-lg">
            No benchmarks run yet.
          </div>
        </div>

        <!-- Default Layer: Forecast Style -->
        <div class="pt-6 border-t border-[var(--lh-border-subtle)]">
          <h3 class="text-sm font-semibold text-[var(--lh-ink-primary)] mb-2">Forecast style</h3>
          <p class="text-xs text-[var(--lh-ink-secondary)] mb-4">
            Most users can leave this on Balanced.
          </p>
          
          <div class="space-y-3">
            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="radio" :value="'Steady'" :checked="reactivityPreset === 'Steady'" @change="$emit('change-reactivity', 'Steady')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
              <span class="text-sm text-[var(--lh-ink-primary)]">Steady</span>
            </label>
            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="radio" :value="'Balanced'" :checked="reactivityPreset === 'Balanced'" @change="$emit('change-reactivity', 'Balanced')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
              <span class="text-sm text-[var(--lh-ink-primary)]">Balanced</span>
            </label>
            <label class="flex items-center space-x-3 cursor-pointer">
              <input type="radio" :value="'Quick to adapt'" :checked="reactivityPreset === 'Quick to adapt'" @change="$emit('change-reactivity', 'Quick to adapt')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
              <span class="text-sm text-[var(--lh-ink-primary)]">Quick to adapt</span>
            </label>
          </div>
        </div>

        <!-- Advanced Layer -->
        <div class="pt-6 border-t border-[var(--lh-border-subtle)]">
          <details class="group">
            <summary class="flex items-center justify-between cursor-pointer list-none font-semibold text-sm text-[var(--lh-ink-primary)] mb-2 outline-none focus-visible:ring-2 focus-visible:ring-[var(--lh-brand)] rounded">
              <span>Advanced forecast settings</span>
              <UIcon name="i-lucide-chevron-down" class="w-4 h-4 transition-transform group-open:rotate-180" />
            </summary>
            
            <p class="text-xs text-[var(--lh-ink-secondary)] mb-4">
              If you already know forecasting terms, you can adjust them here. Most users can leave these unchanged.
            </p>

            <div class="space-y-6 mt-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-[var(--lh-border-subtle)]">
              <!-- Engine Override -->
              <div>
                <h4 class="text-xs font-semibold text-[var(--lh-ink-primary)] mb-3">Engine Override</h4>
                <div class="space-y-3">
                  <label class="flex items-center space-x-3 cursor-pointer">
                    <input type="radio" :value="'auto'" :checked="overrideSelection === 'auto'" @change="$emit('change-override', 'auto')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
                    <span class="text-sm text-[var(--lh-ink-primary)]">Auto-Select (Recommended)</span>
                  </label>
                  <label class="flex items-center space-x-3 cursor-pointer">
                    <input type="radio" :value="'Rust_Croston'" :checked="overrideSelection === 'Rust_Croston'" @change="$emit('change-override', 'Rust_Croston')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
                    <span class="text-sm text-[var(--lh-ink-primary)]">Force Native Rust (Croston)</span>
                  </label>
                  <label class="flex items-center space-x-3 cursor-pointer">
                    <input type="radio" :value="'TimesFM_2.5_ONNX'" :checked="overrideSelection === 'TimesFM_2.5_ONNX'" @change="$emit('change-override', 'TimesFM_2.5_ONNX')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
                    <span class="text-sm text-[var(--lh-ink-primary)]">Force AI Pack (TimesFM ONNX)</span>
                  </label>
                  <label class="flex items-center space-x-3 cursor-pointer">
                    <input type="radio" :value="'Baseline_LastKnown'" :checked="overrideSelection === 'Baseline_LastKnown'" @change="$emit('change-override', 'Baseline_LastKnown')" class="text-[var(--lh-brand)] focus:ring-[var(--lh-brand)]" />
                    <span class="text-sm text-[var(--lh-ink-primary)]">Force Baseline (Last Known)</span>
                  </label>
                </div>
              </div>

              <!-- Alpha Override -->
              <div v-if="overrideSelection === 'Rust_Croston' || overrideSelection === 'auto'">
                <h4 class="text-xs font-semibold text-[var(--lh-ink-primary)] mb-2">Custom Alpha Smoothing (Croston)</h4>
                <div class="flex items-center space-x-3">
                  <input type="number" step="0.01" min="0" max="1" 
                         :value="alphaOverride" 
                         @input="e => $emit('change-alpha', (e.target as HTMLInputElement).value ? parseFloat((e.target as HTMLInputElement).value) : null)"
                         class="block w-24 rounded-md border-gray-300 shadow-sm focus:border-[var(--lh-brand)] focus:ring-[var(--lh-brand)] sm:text-sm text-black dark:text-white dark:bg-gray-700 bg-white" 
                         placeholder="Auto" />
                  <span class="text-xs text-[var(--lh-ink-secondary)]">Valid range: 0.0 - 1.0</span>
                </div>
              </div>

              <!-- Reset Button -->
              <div class="pt-4 border-t border-[var(--lh-border-subtle)] flex justify-end">
                <button @click="$emit('reset-advanced')" class="text-xs font-medium text-red-600 hover:text-red-500 transition-colors">
                  Reset to default
                </button>
              </div>
            </div>
          </details>
        </div>

      </div>
    </div>
  </USlideover>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EngineScore } from '../../../composables/useForecasting'
import type { Item } from '../../../types/domain'

const props = defineProps<{
  modelValue: boolean
  item: Item | null
  loadingScores: boolean
  isRunningBacktest: boolean
  scores: EngineScore[]
  bestEngine: string
  overrideSelection: string
  reactivityPreset: string
  alphaOverride: number | null
}>()

const emit = defineEmits(['update:modelValue', 'run-backtest', 'change-override', 'change-reactivity', 'change-alpha', 'reset-advanced'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isLocked = computed(() => props.overrideSelection !== 'auto')

const selectedEngineDisplay = computed(() => {
  const engine = isLocked.value ? props.overrideSelection : props.bestEngine
  return formatEngineName(engine)
})

const sortedScores = computed(() => {
  return [...props.scores].sort((a, b) => {
    const aMase = a.mase ?? 999999
    const bMase = b.mase ?? 999999
    return aMase - bMase
  })
})

function formatEngineName(name: string) {
  if (name === 'Rust_Croston') return 'Native Rust (Croston)'
  if (name === 'Baseline_LastKnown') return 'Baseline (Last Known)'
  if (name === 'TimesFM_2.5_ONNX') return 'AI Pack (TimesFM ONNX)'
  return name
}
</script>
