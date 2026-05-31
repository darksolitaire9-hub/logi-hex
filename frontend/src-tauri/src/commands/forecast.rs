use sqlx::Row;
use tauri::State;

/// Applies a deterministic human override delta across a forecast trajectory.
/// Returns an error if any adjusted day would go below zero.
pub fn apply_human_override(base_forecast: &[f64], adjustment_qty: f64) -> Result<Vec<f64>, String> {
    let horizon = base_forecast.len();
    if horizon == 0 {
        return Ok(Vec::new());
    }
    let daily_delta = adjustment_qty / horizon as f64;
    
    let mut adjusted = Vec::with_capacity(horizon);
    for (i, &val) in base_forecast.iter().enumerate() {
        let new_val = val + daily_delta;
        if new_val < 0.0 {
            return Err(format!(
                "Adjustment of {} units drives daily prediction below zero on Day {} (value would be {:.2}).",
                adjustment_qty,
                i + 1,
                new_val
            ));
        }
        adjusted.push(new_val);
    }
    Ok(adjusted)
}

/// Helper function to load alpha settings from database.
pub async fn get_alpha_setting(item_id: &str, db_pool: &sqlx::SqlitePool) -> Result<f64, String> {
    let settings = sqlx::query(
        "SELECT reactivity_preset, alpha_override FROM item_forecasting_settings WHERE item_id = ?"
    )
    .bind(item_id)
    .fetch_optional(db_pool)
    .await
    .map_err(|e| format!("Failed to fetch settings: {}", e))?;

    let mut alpha = 0.2; // Default Balanced
    if let Some(row) = settings {
        let preset: String = row.get("reactivity_preset");
        let override_val: Option<f64> = row.get("alpha_override");
        
        if let Some(val) = override_val {
            alpha = val;
        } else {
            alpha = match preset.as_str() {
                "Steady" => 0.1,
                "Quick to adapt" => 0.4,
                _ => 0.2, // Balanced
            };
        }
    }
    Ok(alpha)
}

/// Core implementation for generating a forecast, applying overrides, and writing the audit log atomically.
pub async fn run_ml_forecast_impl(
    app_handle: Option<&tauri::AppHandle>,
    item_id: &str,
    horizon: u32,
    human_adjustment_qty: f64,
    override_reason: &str,
    db_pool: &sqlx::SqlitePool,
) -> Result<crate::types::ForecastResponse, String> {
    // 1. DATA GRAVITY: Fetch data directly from SQLite using fetch_item_demand_history
    let history = fetch_item_demand_history(item_id, db_pool).await?;

    if history.is_empty() {
        return Err("No history found for item".to_string());
    }

    // 2. Resolve engine dynamically
    let engine_name = resolve_forecasting_engine(item_id, horizon as usize, db_pool).await?;

    // 3. Execute chosen engine
    let forecast = if let Some(handle) = app_handle {
        use tauri::Manager;
        match engine_name.as_str() {
            "TimesFM_2.5_ONNX" => {
                let input_history = if history.len() < 14 {
                    let mut padded = vec![0.0; 14];
                    let offset = 14 - history.len();
                    padded[offset..].copy_from_slice(&history);
                    padded
                } else {
                    history.clone()
                };
                let ai_state = handle.state::<crate::ai::state::AiStateManager>();
                let mut engine_guard = ai_state.get_or_load_engine(handle).await?;
                if let Some(engine) = engine_guard.as_mut() {
                    engine.predict(&input_history, horizon as usize)?
                } else {
                    return Err("Engine loaded but reference is null".to_string());
                }
            }
            "Rust_Croston" => {
                let alpha = get_alpha_setting(item_id, db_pool).await?;
                crate::ai::croston::croston_forecast(&history, horizon as usize, alpha)
            }
            _ => {
                crate::ai::orchestrator::last_known_demand_forecast(&history, horizon as usize)
            }
        }
    } else {
        // Mock prediction for unit tests
        vec![10.0; horizon as usize]
    };

    // 4. Validate and apply override
    let adjusted_forecast = if human_adjustment_qty != 0.0 {
        if override_reason.trim().is_empty() {
            return Err("Override reason is required for non-zero adjustments.".to_string());
        }
        apply_human_override(&forecast, human_adjustment_qty)?
    } else {
        forecast.clone()
    };

    // 5. Save audit log row atomically
    let total_base: f64 = forecast.iter().sum();
    let total_final: f64 = adjusted_forecast.iter().sum();
    let input_snapshot = serde_json::to_string(&history).unwrap_or_else(|_| "[]".to_string());

    sqlx::query(
        "INSERT INTO forecast_audit_logs
         (item_id, model_used, input_snapshot, base_prediction,
          human_override_percentage, human_adjustment_qty, override_reason, final_prediction)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    .bind(item_id)
    .bind(&engine_name)
    .bind(&input_snapshot)
    .bind(total_base)
    .bind(0.0) // human_override_percentage (deprecated)
    .bind(human_adjustment_qty)
    .bind(override_reason)
    .bind(total_final)
    .execute(db_pool)
    .await
    .map_err(|e| format!("Failed to save forecast audit: {}", e))?;

    Ok(crate::types::ForecastResponse {
        forecast: adjusted_forecast,
        engine_name,
    })
}

#[tauri::command]
pub async fn save_forecasting_settings(
    item_id: String,
    selected_engine: String,
    locked: bool,
    reactivity_preset: String,
    alpha_override: Option<f64>,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<(), String> {
    sqlx::query(
        "INSERT INTO item_forecasting_settings 
         (item_id, selected_engine, locked, reactivity_preset, alpha_override) 
         VALUES (?, ?, ?, ?, ?)
         ON CONFLICT(item_id) DO UPDATE SET 
           selected_engine=EXCLUDED.selected_engine,
           locked=EXCLUDED.locked,
           reactivity_preset=EXCLUDED.reactivity_preset,
           alpha_override=EXCLUDED.alpha_override"
    )
    .bind(&item_id)
    .bind(&selected_engine)
    .bind(locked)
    .bind(&reactivity_preset)
    .bind(alpha_override)
    .execute(&*db_pool)
    .await
    .map_err(|e| format!("Failed to save forecasting settings: {}", e))?;

    Ok(())
}

#[tauri::command]
pub async fn get_forecasting_settings(
    item_id: String,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<Option<crate::types::ForecastingSettings>, String> {
    let row = sqlx::query(
        "SELECT selected_engine, locked, reactivity_preset, alpha_override 
         FROM item_forecasting_settings 
         WHERE item_id = ?"
    )
    .bind(&item_id)
    .fetch_optional(&*db_pool)
    .await
    .map_err(|e| format!("Failed to fetch forecasting settings: {}", e))?;

    if let Some(r) = row {
        let selected_engine: String = r.get("selected_engine");
        let locked: bool = r.get("locked");
        let reactivity_preset: String = r.get("reactivity_preset");
        let alpha_override: Option<f64> = r.get("alpha_override");
        Ok(Some(crate::types::ForecastingSettings {
            item_id,
            selected_engine,
            locked,
            reactivity_preset,
            alpha_override,
        }))
    } else {
        Ok(None)
    }
}

#[tauri::command]
pub async fn get_backtest_scores(
    item_id: String,
    horizon: usize,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<Vec<crate::ai::orchestrator::EngineScore>, String> {
    let rows = sqlx::query(
        "SELECT engine_name, wape, mase, bias 
         FROM engine_backtest_scores 
         WHERE item_id = ? AND horizon_days = ?"
    )
    .bind(&item_id)
    .bind(horizon as i64)
    .fetch_all(&*db_pool)
    .await
    .map_err(|e| format!("Failed to fetch backtest scores: {}", e))?;

    let mut scores = Vec::new();
    for r in rows {
        let engine_name: String = r.get("engine_name");
        let wape: Option<f64> = r.get("wape");
        let mase: Option<f64> = r.get("mase");
        let bias: Option<f64> = r.get("bias");
        scores.push(crate::ai::orchestrator::EngineScore {
            engine_name,
            wape,
            mase,
            bias,
        });
    }
    Ok(scores)
}

#[tauri::command]
pub async fn get_best_forecasting_engine(
    item_id: String,
    horizon: usize,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<String, String> {
    resolve_forecasting_engine(&item_id, horizon, &*db_pool).await
}

/// Runs the walk-forward backtest simulation and saves scores to SQLite.
/// DATA GRAVITY: Rust fetches historical demand directly from SQLite.
/// Vue passes item_id + horizon — never the raw history array.
#[tauri::command]
pub async fn run_backtest(
    app_handle: tauri::AppHandle,
    item_id: String,
    horizon: usize,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<Vec<crate::ai::orchestrator::EngineScore>, String> {
    use tauri::Manager;

    // DATA GRAVITY: fetch history using fetch_item_demand_history
    let history = fetch_item_demand_history(&item_id, &*db_pool).await?;

    if history.is_empty() {
        return Err(format!("No movement history found for item '{}'", item_id));
    }

    let mut model_dir = app_handle.path().app_data_dir()
        .map_err(|_| "Failed to resolve app data dir".to_string())?;
    model_dir.push("models");

    let alpha = get_alpha_setting(&item_id, &*db_pool).await?;

    let scores = crate::ai::orchestrator::run_backtest_simulation(Some(model_dir), &history, horizon, alpha)?;

    // Save scores to database
    for score in &scores {
        sqlx::query(
            "INSERT OR REPLACE INTO engine_backtest_scores 
             (item_id, engine_name, horizon_days, wape, mase, bias, last_tested_at) 
             VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)"
        )
        .bind(&item_id)
        .bind(&score.engine_name)
        .bind(horizon as i64)
        .bind(score.wape)
        .bind(score.mase)
        .bind(score.bias)
        .execute(&*db_pool)
        .await
        .map_err(|e| format!("Failed to save backtest score: {}", e))?;
    }

    Ok(scores)
}

/// Helper function to parse YYYY-MM-DD to days since Unix epoch.
fn parse_date_to_days(date_str: &str) -> Option<u64> {
    let parts: Vec<&str> = date_str.split('-').collect();
    if parts.len() != 3 {
        return None;
    }
    let y: u64 = parts[0].parse().ok()?;
    let m: u64 = parts[1].parse().ok()?;
    let d: u64 = parts[2].parse().ok()?;
    
    let mut days = 0;
    for year in 1970..y {
        days += if crate::commands::ledger::is_leap(year) { 366 } else { 365 };
    }
    let months = [31, if crate::commands::ledger::is_leap(y) { 29 } else { 28 }, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    for month in 1..(m as usize) {
        days += months[month - 1];
    }
    days += d - 1;
    Some(days)
}

/// Applies Linear Interpolation to mask and fill "Censored Demand" (days with 0 stock and 0 usage).
fn interpolate_censored_demand(raw_demand: &[Option<f64>]) -> Vec<f64> {
    let mut history = Vec::with_capacity(raw_demand.len());
    
    for i in 0..raw_demand.len() {
        if let Some(val) = raw_demand[i] {
            history.push(val);
            continue;
        }
        
        // Find next known value
        let mut next_idx = i + 1;
        while next_idx < raw_demand.len() && raw_demand[next_idx].is_none() {
            next_idx += 1;
        }
        
        // Find previous known value
        let mut prev_idx = i as i64 - 1;
        while prev_idx >= 0 && raw_demand[prev_idx as usize].is_none() {
            prev_idx -= 1;
        }
        
        let mut next_val = if next_idx < raw_demand.len() { raw_demand[next_idx] } else { None };
        let mut prev_val = if prev_idx >= 0 { raw_demand[prev_idx as usize] } else { None };
        
        if prev_val.is_none() && next_val.is_none() {
            prev_val = Some(0.0);
            next_val = Some(0.0);
        } else if prev_val.is_none() {
            prev_val = next_val;
        } else if next_val.is_none() {
            next_val = prev_val;
        }
        
        let prev_val = prev_val.unwrap_or(0.0);
        let next_val = next_val.unwrap_or(0.0);
        
        let distance = next_idx as i64 - prev_idx;
        let step = if distance > 0 { (next_val - prev_val) / distance as f64 } else { 0.0 };
        
        history.push(prev_val + step * (i as i64 - prev_idx) as f64);
    }
    
    history
}

/// Fetches the item's historical demand with gap-filling and linear interpolation for censored demand.
pub async fn fetch_item_demand_history(
    item_id: &str,
    db_pool: &sqlx::SqlitePool,
) -> Result<Vec<f64>, String> {
    // 1. Fetch item current stock and timezone
    let item_row = sqlx::query(
        "SELECT i.current_stock, w.timezone 
         FROM items i
         JOIN workspaces w ON i.workspace_id = w.id
         WHERE i.id = ?"
    )
    .bind(item_id)
    .fetch_optional(db_pool)
    .await
    .map_err(|e| format!("Failed to fetch item current stock: {}", e))?;

    let (current_stock, timezone) = match item_row {
        Some(row) => {
            let stock: f64 = row.get("current_stock");
            let tz: String = row.get("timezone");
            (stock, tz)
        }
        None => return Err(format!("Item '{}' not found", item_id)),
    };

    // 2. Query daily demand and net changes
    let rows = sqlx::query(
        "SELECT 
           m.local_date as date,
           SUM(CASE WHEN m.direction IN ('SEND', 'USE') THEN mli.quantity ELSE 0.0 END) as demand_qty,
           SUM(CASE 
                 WHEN m.direction IN ('RECEIVE', 'CORRECT', 'COLLECT') THEN mli.quantity 
                 WHEN m.direction IN ('SEND', 'USE') THEN -mli.quantity
                 ELSE 0.0 
               END) as net_change
         FROM movement_line_items mli
         JOIN movements m ON mli.movement_id = m.id
         WHERE mli.item_id = ?
         GROUP BY m.local_date
         ORDER BY m.local_date ASC"
    )
    .bind(item_id)
    .fetch_all(db_pool)
    .await
    .map_err(|e| format!("Failed to fetch demand history rows: {}", e))?;

    if rows.is_empty() {
        return Ok(Vec::new());
    }

    use std::collections::HashMap;
    let mut demand_by_date = HashMap::new();
    let mut net_change_by_date = HashMap::new();
    let mut first_date_str = String::new();

    for (i, row) in rows.iter().enumerate() {
        let date_str: String = row.get("date");
        if i == 0 {
            first_date_str = date_str.clone();
        }
        let demand_qty: f64 = row.get("demand_qty");
        let net_change: f64 = row.get("net_change");
        demand_by_date.insert(date_str.clone(), demand_qty);
        net_change_by_date.insert(date_str, net_change);
    }

    // Get today's local date string using timezone
    let today_str = crate::commands::ledger::chrono_tz_local_date(&timezone);

    // Parse start and end date into days
    let start_days = parse_date_to_days(&first_date_str)
        .ok_or_else(|| format!("Invalid start date format: {}", first_date_str))?;
    let end_days = parse_date_to_days(&today_str)
        .ok_or_else(|| format!("Invalid today date format: {}", today_str))?;

    // If start_days is after end_days, align them
    let start_days = if start_days > end_days { end_days } else { start_days };

    // Generate continuous date strings
    let mut dates = Vec::new();
    for day in start_days..=end_days {
        dates.push(crate::commands::ledger::chrono_days_to_date(day));
    }

    // Reconstruct historical stock balances (Backwards Replay)
    let mut stock_by_date = HashMap::new();
    let mut running_stock = current_stock;
    for date_str in dates.iter().rev() {
        stock_by_date.insert(date_str.clone(), running_stock);
        let net_change = net_change_by_date.get(date_str).copied().unwrap_or(0.0);
        running_stock -= net_change;
    }

    // Identify Censored Demand (0 stock and 0 usage)
    let mut raw_demand = Vec::new();
    for date_str in &dates {
        let stock = stock_by_date.get(date_str).copied().unwrap_or(0.0);
        let demand = demand_by_date.get(date_str).copied().unwrap_or(0.0);
        
        if stock <= 0.0 && demand == 0.0 {
            raw_demand.push(None); // Mask for interpolation
        } else {
            raw_demand.push(Some(demand));
        }
    }

    // Perform Linear Interpolation
    let history = interpolate_censored_demand(&raw_demand);
    Ok(history)
}

/// Resolves the forecasting engine to use based on settings and backtest scores.
pub async fn resolve_forecasting_engine(
    item_id: &str,
    horizon_days: usize,
    db_pool: &sqlx::SqlitePool,
) -> Result<String, String> {
    // 1. Check if user has locked an engine override
    let settings = sqlx::query(
        "SELECT selected_engine, locked FROM item_forecasting_settings WHERE item_id = ?"
    )
    .bind(item_id)
    .fetch_optional(db_pool)
    .await
    .map_err(|e| format!("Failed to fetch settings: {}", e))?;

    if let Some(row) = settings {
        let locked: bool = row.get("locked");
        let selected_engine: String = row.get("selected_engine");
        if locked && selected_engine != "AUTO" {
            return Ok(selected_engine);
        }
    }

    // 2. Otherwise, auto-select based on lowest MASE, then WAPE.
    let score_row = sqlx::query(
        "SELECT engine_name 
         FROM engine_backtest_scores 
         WHERE item_id = ? AND horizon_days = ?
         ORDER BY 
           IFNULL(mase, 999999.0) ASC, 
           IFNULL(wape, 999999.0) ASC, 
           ABS(IFNULL(bias, 999999.0)) ASC
         LIMIT 1"
    )
    .bind(item_id)
    .bind(horizon_days as i64)
    .fetch_optional(db_pool)
    .await
    .map_err(|e| format!("Failed to query best engine: {}", e))?;

    if let Some(row) = score_row {
        let engine: String = row.get("engine_name");
        return Ok(engine);
    }

    // Default Fallback if no scores exist
    Ok("Baseline_LastKnown".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rust_apply_human_override_valid() {
        let base = vec![10.0, 20.0, 30.0];
        let res = apply_human_override(&base, 15.0).unwrap();
        assert_eq!(res, vec![15.0, 25.0, 35.0]);
    }

    #[test]
    fn test_rust_apply_human_override_negative_valid() {
        let base = vec![10.0, 20.0, 30.0];
        let res = apply_human_override(&base, -15.0).unwrap();
        assert_eq!(res, vec![5.0, 15.0, 25.0]);
    }

    #[test]
    fn test_rust_apply_human_override_below_zero() {
        let base = vec![10.0, 20.0, 30.0];
        let res = apply_human_override(&base, -40.0);
        assert!(res.is_err());
        assert!(res.unwrap_err().contains("drives daily prediction below zero"));
    }

    #[test]
    fn test_resolve_forecasting_engine_rules() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let pool = sqlx::SqlitePool::connect("sqlite::memory:").await.unwrap();
            
            sqlx::query(
                "CREATE TABLE items (
                    id TEXT PRIMARY KEY,
                    current_stock REAL
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE item_forecasting_settings (
                    item_id TEXT PRIMARY KEY,
                    selected_engine TEXT NOT NULL DEFAULT 'AUTO',
                    locked BOOLEAN NOT NULL DEFAULT 0,
                    reactivity_preset TEXT NOT NULL DEFAULT 'Balanced',
                    alpha_override REAL
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE engine_backtest_scores (
                    item_id TEXT NOT NULL,
                    engine_name TEXT NOT NULL,
                    horizon_days INTEGER NOT NULL,
                    wape REAL,
                    mase REAL,
                    bias REAL,
                    last_tested_at DATETIME,
                    PRIMARY KEY (item_id, engine_name, horizon_days)
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query("INSERT INTO items (id, current_stock) VALUES ('item1', 10.0)")
                .execute(&pool).await.unwrap();

            let resolved = resolve_forecasting_engine("item1", 14, &pool).await.unwrap();
            assert_eq!(resolved, "Baseline_LastKnown");

            sqlx::query("INSERT INTO engine_backtest_scores (item_id, engine_name, horizon_days, wape, mase, bias) VALUES ('item1', 'EngineA', 14, 0.2, 0.5, 0.0)")
                .execute(&pool).await.unwrap();
            sqlx::query("INSERT INTO engine_backtest_scores (item_id, engine_name, horizon_days, wape, mase, bias) VALUES ('item1', 'EngineB', 14, 0.1, 0.8, 0.0)")
                .execute(&pool).await.unwrap();

            let resolved = resolve_forecasting_engine("item1", 14, &pool).await.unwrap();
            assert_eq!(resolved, "EngineA");

            sqlx::query("INSERT INTO item_forecasting_settings (item_id, selected_engine, locked) VALUES ('item1', 'EngineB', 1)")
                .execute(&pool).await.unwrap();

            let resolved = resolve_forecasting_engine("item1", 14, &pool).await.unwrap();
            assert_eq!(resolved, "EngineB");
        });
    }

    #[test]
    fn test_forecast_atomic_audit_log() {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            let pool = sqlx::SqlitePool::connect("sqlite::memory:").await.unwrap();
            
            sqlx::query(
                "CREATE TABLE items (
                    id TEXT PRIMARY KEY,
                    current_stock REAL,
                    workspace_id TEXT
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE workspaces (
                    id TEXT PRIMARY KEY,
                    timezone TEXT
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE movements (
                    id TEXT PRIMARY KEY,
                    local_date TEXT,
                    direction TEXT,
                    workspace_id TEXT
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE movement_line_items (
                    movement_id TEXT,
                    item_id TEXT,
                    quantity REAL
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE forecast_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    input_snapshot TEXT NOT NULL,
                    base_prediction REAL NOT NULL,
                    human_override_percentage REAL DEFAULT 0,
                    human_adjustment_qty REAL DEFAULT 0,
                    override_reason TEXT,
                    final_prediction REAL NOT NULL
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE item_forecasting_settings (
                    item_id TEXT PRIMARY KEY,
                    selected_engine TEXT NOT NULL DEFAULT 'AUTO',
                    locked BOOLEAN NOT NULL DEFAULT 0,
                    reactivity_preset TEXT NOT NULL DEFAULT 'Balanced',
                    alpha_override REAL
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query(
                "CREATE TABLE engine_backtest_scores (
                    item_id TEXT NOT NULL,
                    engine_name TEXT NOT NULL,
                    horizon_days INTEGER NOT NULL,
                    wape REAL,
                    mase REAL,
                    bias REAL,
                    last_tested_at DATETIME,
                    PRIMARY KEY (item_id, engine_name, horizon_days)
                 )"
            ).execute(&pool).await.unwrap();

            sqlx::query("INSERT INTO workspaces (id, timezone) VALUES ('ws1', 'UTC')").execute(&pool).await.unwrap();
            sqlx::query("INSERT INTO items (id, current_stock, workspace_id) VALUES ('item1', 10.0, 'ws1')").execute(&pool).await.unwrap();
            sqlx::query("INSERT INTO movements (id, local_date, direction, workspace_id) VALUES ('m1', '2026-05-01', 'SEND', 'ws1')").execute(&pool).await.unwrap();
            sqlx::query("INSERT INTO movement_line_items (movement_id, item_id, quantity) VALUES ('m1', 'item1', 5.0)").execute(&pool).await.unwrap();

            let res = run_ml_forecast_impl(
                None,
                "item1",
                3,
                15.0,
                "Test positive adjustment",
                &pool,
            ).await.unwrap();

            assert_eq!(res.forecast, vec![15.0, 15.0, 15.0]);

            let audit_count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM forecast_audit_logs")
                .fetch_one(&pool).await.unwrap();
            assert_eq!(audit_count, 1);

            let err_res = run_ml_forecast_impl(
                None,
                "item1",
                3,
                -45.0,
                "Test invalid negative adjustment",
                &pool,
            ).await;

            assert!(err_res.is_err());
            assert!(err_res.unwrap_err().contains("drives daily prediction below zero"));

            let audit_count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM forecast_audit_logs")
                .fetch_one(&pool).await.unwrap();
            assert_eq!(audit_count, 1);
        });
    }
}
