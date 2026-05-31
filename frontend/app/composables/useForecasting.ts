import { invoke } from '@tauri-apps/api/core'
import type { ForecastingSettings } from '../types/generated/ForecastingSettings'

export interface EngineScore {
  engine_name: string
  wape: number | null
  mase: number | null
  bias: number | null
}

export interface ItemForecastingSettings {
  item_id: string
  locked_engine_name: string | null
  is_locked: boolean
  reactivity_preset: string
  alpha_override: number | null
}

export const useForecasting = () => {
  // Trigger the Rust Walk-Forward Backtester (scores are automatically saved in SQLite in Rust)
  const triggerBacktest = async (itemId: string, horizonDays: number) => {
    return await invoke<EngineScore[]>('run_backtest', { itemId, horizon: horizonDays })
  }

  // Retrieve scores for an item to explain the choice to the user
  const getScores = async (itemId: string, horizonDays: number): Promise<EngineScore[]> => {
    return await invoke<EngineScore[]>('get_backtest_scores', { itemId, horizon: horizonDays })
  }

  // Auto-Select the best engine based on pure WAPE/MASE/Bias ranking
  const getBestEngine = async (itemId: string, horizonDays: number): Promise<string> => {
    return await invoke<string>('get_best_forecasting_engine', { itemId, horizon: horizonDays })
  }

  // Retrieve current settings and lock status for an item
  const getSettings = async (itemId: string): Promise<ItemForecastingSettings | null> => {
    const settings = await invoke<ForecastingSettings | null>('get_forecasting_settings', { itemId })
    if (settings) {
      return {
        item_id: itemId,
        locked_engine_name: settings.selected_engine,
        is_locked: settings.locked,
        reactivity_preset: settings.reactivity_preset || 'Balanced',
        alpha_override: settings.alpha_override
      }
    }
    return null
  }
  
  // Apply User Overrides
  const setUserOverride = async (itemId: string, engineName: string | null, isLocked: boolean, reactivityPreset: string = 'Balanced', alphaOverride: number | null = null) => {
    await invoke('save_forecasting_settings', {
      itemId,
      selectedEngine: engineName || 'AUTO',
      locked: isLocked,
      reactivityPreset,
      alphaOverride
    })
  }

  return {
    triggerBacktest,
    getScores,
    getBestEngine,
    getSettings,
    setUserOverride
  }
}

