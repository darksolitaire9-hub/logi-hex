use sqlx::Row;
use tauri::State;
use crate::types::ForecastAuditCommand;

/// Saves a forecast audit log row.
/// All forecast writes now route through Rust — Vue no longer touches the audit table.
#[tauri::command]
pub async fn save_forecast_audit(
    payload: ForecastAuditCommand,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<(), String> {
    sqlx::query(
        "INSERT INTO forecast_audit_logs
         (item_id, model_used, input_snapshot, base_prediction,
          human_override_percentage, human_adjustment_qty, override_reason, final_prediction)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    )
    .bind(&payload.item_id)
    .bind(&payload.model_used)
    .bind(&payload.input_snapshot)
    .bind(payload.base_prediction)
    .bind(payload.human_override_percentage)
    .bind(payload.human_adjustment_qty)
    .bind(&payload.override_reason)
    .bind(payload.final_prediction)
    .execute(&*db_pool)
    .await
    .map_err(|e| format!("Failed to save forecast audit: {}", e))?;

    Ok(())
}

/// Runs the walk-forward backtest simulation.
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

    crate::ai::orchestrator::run_backtest_simulation(Some(model_dir), &history, horizon)
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
