import { useDatabase } from './useDatabase'
import { invoke } from '@tauri-apps/api/core'

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
}

export const useForecasting = () => {
  // Save new backtest scores into SQLite securely using UPSERT (ON CONFLICT REPLACE)
  const saveBacktestScores = async (itemId: string, horizonDays: number, scores: EngineScore[]) => {
    const db = await useDatabase()
    
    // SQLite UPSERT via INSERT OR REPLACE using our composite primary key (item_id, engine_name, horizon_days)
    for (const score of scores) {
      await db.execute(
        `INSERT OR REPLACE INTO engine_backtest_scores 
        (item_id, engine_name, horizon_days, wape, mase, bias, last_tested_at) 
        VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)`,
        [itemId, score.engine_name, horizonDays, score.wape, score.mase, score.bias]
      )
    }
  }

  // Trigger the Rust Walk-Forward Backtester and immediately save scores to DB
  const triggerBacktest = async (itemId: string, history: number[], horizonDays: number) => {
    // 1. Invoke Rust backend mathematically
    const scores = await invoke<EngineScore[]>('trigger_backtest', { history, horizon: horizonDays })
    
    // 2. Save scores to local SQLite
    await saveBacktestScores(itemId, horizonDays, scores)
    
    return scores
  }

  // Retrieve scores for an item to explain the choice to the user
  const getScores = async (itemId: string, horizonDays: number): Promise<EngineScore[]> => {
    const db = await useDatabase()
    return await db.select<EngineScore[]>(
      `SELECT engine_name, wape, mase, bias 
       FROM engine_backtest_scores 
       WHERE item_id = $1 AND horizon_days = $2`,
      [itemId, horizonDays]
    )
  }

  // Auto-Select the best engine based on pure WAPE/MASE/Bias ranking
  const getBestEngine = async (itemId: string, horizonDays: number): Promise<string> => {
    const db = await useDatabase()
    
    // Check if user has hard-locked an engine override
    const settings = await db.select<{ locked_engine_name: string }[]>(
      `SELECT locked_engine_name FROM item_forecasting_settings WHERE item_id = $1 AND is_locked = 1`,
      [itemId]
    )
    if (settings.length > 0 && settings[0].locked_engine_name) {
      return settings[0].locked_engine_name
    }

    // Otherwise, auto-select based on lowest MASE (primary for sparse data), then WAPE.
    // We sort NULLs to the bottom by using IFNULL(mase, 999999).
    const topEngines = await db.select<{ engine_name: string }[]>(
      `SELECT engine_name 
       FROM engine_backtest_scores 
       WHERE item_id = $1 AND horizon_days = $2
       ORDER BY 
         IFNULL(mase, 999999.0) ASC, 
         IFNULL(wape, 999999.0) ASC, 
         ABS(IFNULL(bias, 999999.0)) ASC
       LIMIT 1`,
      [itemId, horizonDays]
    )

    if (topEngines.length > 0) {
      return topEngines[0].engine_name
    }

    // Default Fallback if no scores exist
    return "Baseline_LastKnown"
  }
  
  // Apply User Overrides
  const setUserOverride = async (itemId: string, engineName: string | null, isLocked: boolean) => {
    const db = await useDatabase()
    await db.execute(
      `INSERT OR REPLACE INTO item_forecasting_settings 
       (item_id, locked_engine_name, is_locked) 
       VALUES ($1, $2, $3)`,
      [itemId, engineName, isLocked ? 1 : 0]
    )
  }

  return {
    triggerBacktest,
    getScores,
    getBestEngine,
    setUserOverride
  }
}
