pub mod db;
pub mod ai;
pub mod commands;
pub mod crypto;
pub mod types;

use tauri::{Manager, RunEvent};
use sqlx::Row;

#[tauri::command]
fn generate_statistical_forecast(history: Vec<f64>, horizon: usize) -> Result<Vec<f64>, String> {
    // 0.1 is a standard smoothing parameter for alpha. In a full system, this can be auto-tuned.
    let forecast = crate::ai::croston::croston_forecast(&history, horizon, 0.1);
    Ok(forecast)
}

#[tauri::command]
async fn download_ai_pack(app_handle: tauri::AppHandle, url: String, expected_sha256: String, filename: String) -> Result<String, String> {
    let path = crate::ai::download::download_ai_pack(app_handle, &url, &expected_sha256, &filename).await?;
    Ok(path.to_string_lossy().to_string())
}

#[tauri::command]
async fn run_ml_forecast(
    app_handle: tauri::AppHandle, 
    item_id: String, 
    horizon: u32,
    human_adjustment_qty: f64,
    override_reason: String,
    db_pool: tauri::State<'_, sqlx::SqlitePool>
) -> Result<String, String> {
    let response = crate::commands::forecast::run_ml_forecast_impl(
        Some(&app_handle),
        &item_id,
        horizon,
        human_adjustment_qty,
        &override_reason,
        &*db_pool,
    )
    .await?;

    // Return compact JSON result
    serde_json::to_string(&response).map_err(|e| e.to_string())
}

#[tauri::command]
async fn get_ai_status(ai_state: tauri::State<'_, crate::ai::state::AiStateManager>) -> Result<crate::ai::state::AiEngineStatus, String> {
    let status = ai_state.status.read().await;
    Ok(status.clone())
}

#[tauri::command]
async fn warmup_ai_engine(app_handle: tauri::AppHandle, ai_state: tauri::State<'_, crate::ai::state::AiStateManager>) -> Result<(), String> {
    ai_state.warmup_engine(&app_handle).await
}

fn verify_export_path_rules(input_path: &str) -> Result<std::path::PathBuf, String> {
    let trimmed = input_path.trim();
    if trimmed.is_empty() {
        return Err("Path cannot be empty".to_string());
    }

    let path = std::path::Path::new(trimmed);
    
    // 1. Strictly reject path traversal components
    for component in path.components() {
        match component {
            std::path::Component::ParentDir => {
                return Err("Path traversal (..) is not allowed".to_string());
            }
            _ => {}
        }
    }
    
    Ok(path.to_path_buf())
}

fn verify_and_resolve_path(app_handle: &tauri::AppHandle, input_path: &str) -> Result<std::path::PathBuf, String> {
    let path = verify_export_path_rules(input_path)?;
    let trimmed = input_path.trim();

    // 2. Determine if it is a filename only (no separators)
    let is_filename_only = !trimmed.contains('/') && !trimmed.contains('\\');
    if is_filename_only {
        let base_dir = app_handle.path().download_dir()
            .or_else(|_| app_handle.path().document_dir())
            .or_else(|_| app_handle.path().app_data_dir())
            .map_err(|_| "Failed to resolve any safe base directory".to_string())?;
        return Ok(base_dir.join(path));
    }

    // 3. Resolve the parent directory
    let parent = path.parent().ok_or_else(|| "Path has no parent directory".to_string())?;
    
    // Canonicalize parent directory to check safety. Parent must exist.
    let canonical_parent = parent.canonicalize()
        .map_err(|e| format!("Parent directory does not exist or is invalid: {}", e))?;

    // 4. Resolve safe system directories
    let allowed_dirs = vec![
        app_handle.path().download_dir(),
        app_handle.path().document_dir(),
        app_handle.path().desktop_dir(),
        app_handle.path().app_data_dir(),
    ];

    let mut is_under_allowed = false;
    for allowed_dir_res in allowed_dirs {
        if let Ok(allowed_dir) = allowed_dir_res {
            if let Ok(canonical_allowed) = allowed_dir.canonicalize() {
                if canonical_parent.starts_with(&canonical_allowed) {
                    is_under_allowed = true;
                    break;
                }
            }
        }
    }

    if !is_under_allowed {
        return Err("Target path is outside allowed directories".to_string());
    }

    let filename = path.file_name().ok_or_else(|| "Invalid filename".to_string())?;
    Ok(canonical_parent.join(filename))
}

#[tauri::command]
async fn export_csv_to_disk(
    app_handle: tauri::AppHandle,
    item_id: String,
    save_path: String,
    db_pool: tauri::State<'_, sqlx::SqlitePool>
) -> Result<String, String> {
    use std::io::Write;
    
    // Verify and resolve the destination path securely
    let resolved_path = verify_and_resolve_path(&app_handle, &save_path)?;
    
    // Fetch all history
    let records = sqlx::query("SELECT id, direction, timestamp, client_id, notes FROM movements WHERE workspace_id = (SELECT workspace_id FROM items WHERE id = ?) ORDER BY timestamp DESC")
        .bind(&item_id)
        .fetch_all(&*db_pool)
        .await
        .map_err(|e| format!("Failed to fetch movements for CSV: {}", e))?;

    let mut file = std::fs::File::create(&resolved_path).map_err(|e| format!("Failed to create file: {}", e))?;
    
    writeln!(file, "ID,Direction,Timestamp,ClientID,Notes").map_err(|e| e.to_string())?;
    
    let mut count = 0;
    for row in records {
        let notes_opt: Option<String> = row.get("notes");
        let notes = notes_opt.unwrap_or_default().replace("\"", "\"\"");
        
        let id: String = row.get("id");
        let direction: String = row.get("direction");
        let timestamp_opt: Option<String> = row.get("timestamp");
        let client_id_opt: Option<String> = row.get("client_id");
        
        writeln!(
            file, 
            "{},{},{},{},\"{}\"", 
            id, 
            direction, 
            timestamp_opt.unwrap_or_default(), 
            client_id_opt.unwrap_or_default(), 
            notes
        ).map_err(|e| e.to_string())?;
        count += 1;
    }

    Ok(format!("Successfully exported {} rows to {}", count, resolved_path.to_string_lossy()))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            run_ml_forecast, 
            generate_statistical_forecast, 
            crate::commands::forecast::run_backtest,
            crate::commands::forecast::save_forecasting_settings,
            crate::commands::forecast::get_forecasting_settings,
            crate::commands::forecast::get_backtest_scores,
            crate::commands::forecast::get_best_forecasting_engine,
            crate::commands::forecast::get_item_movement_history,
            crate::commands::ledger::log_movement,
            crate::commands::ledger::fetch_client_history,
            crate::commands::ledger::fetch_global_history,
            crate::commands::ledger::get_export_data,
            crate::commands::workspace::get_workspaces,
            crate::commands::workspace::create_workspace,
            crate::commands::client::get_clients,
            crate::commands::client::create_client,
            crate::commands::client::delete_client,
            crate::commands::item::get_items,
            crate::commands::item::create_item,
            crate::commands::item::update_item,
            crate::commands::item::delete_item,
            crate::commands::item::get_low_stock_items,
            download_ai_pack,
            export_csv_to_disk,
            get_ai_status,
            warmup_ai_engine
        ])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let handle = app.handle().clone();
            
            // Initialize AI State Manager
            let ai_manager = crate::ai::state::AiStateManager::new();
            handle.manage(ai_manager);

            // Initialize Crypto State (OS Keyring)
            let master_key = crate::crypto::load_or_create_master_key().unwrap_or_else(|e| {
                log::error!("Failed to init OS keyring: {}", e);
                panic!("Keyring init failed");
            });
            let crypto_state = crate::crypto::state::CryptoState::new(master_key.to_vec());
            handle.manage(crypto_state);

            // Initialize custom SqlitePool (WAL) and MPSC DbWriter
            let handle = app.handle().clone();
            tauri::async_runtime::block_on(async move {
                match db::init_db(&handle).await {
                    Ok(pool) => {
                        let writer = db::writer::DbWriter::new(pool.clone());
                        handle.manage(pool);
                        handle.manage(writer);
                        log::info!("Backend Resolutions: WAL DB Pool & MPSC Queue initialized");
                    }
                    Err(e) => log::error!("Failed to initialize DB Pool: {}", e),
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| match event {
        RunEvent::ExitRequested { .. } => {
            log::info!("Exit requested, draining MPSC write queue...");
            // Best-effort drain on shutdown
            if let Some(writer) = app_handle.try_state::<db::writer::DbWriter>() {
                tauri::async_runtime::block_on(async {
                    writer.shutdown().await;
                });
            }
        }
        _ => {}
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_verify_export_path_rules_valid() {
        assert!(verify_export_path_rules("export.csv").is_ok());
        assert!(verify_export_path_rules("subfolder/export.csv").is_ok());
        assert!(verify_export_path_rules("subfolder\\export.csv").is_ok());
    }

    #[test]
    fn test_verify_export_path_rules_empty() {
        assert!(verify_export_path_rules("").is_err());
        assert!(verify_export_path_rules("   ").is_err());
    }

    #[test]
    fn test_verify_export_path_rules_traversal() {
        assert!(verify_export_path_rules("../export.csv").is_err());
        assert!(verify_export_path_rules("..\\export.csv").is_err());
        assert!(verify_export_path_rules("folder/../export.csv").is_err());
        assert!(verify_export_path_rules("export.csv/..").is_err());
    }
}
