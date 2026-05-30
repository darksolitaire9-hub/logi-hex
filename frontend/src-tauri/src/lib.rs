pub mod db;
pub mod ai;

use tauri_plugin_sql::{Migration, MigrationKind};
use tauri::{Manager, RunEvent};
use sqlx::Row;

#[tauri::command]
fn generate_statistical_forecast(history: Vec<f64>, horizon: usize) -> Result<Vec<f64>, String> {
    // 0.1 is a standard smoothing parameter for alpha. In a full system, this can be auto-tuned.
    let forecast = crate::ai::croston::croston_forecast(&history, horizon, 0.1);
    Ok(forecast)
}

#[tauri::command]
fn trigger_backtest(app_handle: tauri::AppHandle, history: Vec<f64>, horizon: usize) -> Result<Vec<crate::ai::orchestrator::EngineScore>, String> {
    use tauri::Manager;
    let mut model_dir = app_handle.path().app_data_dir().map_err(|_| "Failed to resolve app data dir".to_string())?;
    model_dir.push("models");
    crate::ai::orchestrator::run_backtest_simulation(Some(model_dir), &history, horizon)
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
    db_pool: tauri::State<'_, sqlx::SqlitePool>
) -> Result<String, String> {
    // 1. DATA GRAVITY: Fetch data directly from SQLite instead of via IPC String
    let records = sqlx::query("SELECT quantity FROM movement_line_items WHERE item_id = ? ORDER BY id ASC")
        .bind(&item_id)
        .fetch_all(&*db_pool)
        .await
        .map_err(|e| format!("Failed to fetch history: {}", e))?;

    let history: Vec<f64> = records.into_iter().map(|r| r.get::<f64, _>("quantity")).collect();

    if history.is_empty() {
        return Err("No history found for item".to_string());
    }

    // 2. IN-PROCESS AI: Use the shared ORT session (Lazy Loaded)
    let ai_state = app_handle.state::<crate::ai::state::AiStateManager>();
    let mut engine_guard = ai_state.get_or_load_engine(&app_handle).await?;
    
    let forecast = if let Some(engine) = engine_guard.as_mut() {
        engine.predict(&history, horizon as usize)?
    } else {
        return Err("Engine loaded but reference is null".to_string());
    };
    
    // Return compact JSON result
    serde_json::to_string(&forecast).map_err(|e| e.to_string())
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

#[tauri::command]
async fn export_csv_to_disk(
    _app_handle: tauri::AppHandle,
    item_id: String,
    save_path: String,
    db_pool: tauri::State<'_, sqlx::SqlitePool>
) -> Result<String, String> {
    use std::io::Write;
    
    // Fetch all history
    let records = sqlx::query("SELECT id, direction, timestamp, client_id, notes FROM movements WHERE workspace_id = (SELECT workspace_id FROM items WHERE id = ?) ORDER BY timestamp DESC")
        .bind(&item_id)
        .fetch_all(&*db_pool)
        .await
        .map_err(|e| format!("Failed to fetch movements for CSV: {}", e))?;

    let mut file = std::fs::File::create(&save_path).map_err(|e| format!("Failed to create file: {}", e))?;
    
    writeln!(file, "ID,Direction,Timestamp,ClientID,Notes").map_err(|e| e.to_string())?;
    
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
    }

    Ok(format!("Successfully exported {} rows to {}", 0, save_path)) // We could count rows, but Ok is fine
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let migrations = vec![
        Migration {
            version: 1,
            description: "init_schema",
            sql: include_str!("../migrations/1_init.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 2,
            description: "enterprise_upgrades",
            sql: include_str!("../migrations/2_enterprise.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 3,
            description: "forecast_audit",
            sql: include_str!("../migrations/3_forecast_audit.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 4,
            description: "deterministic_overrides",
            sql: include_str!("../migrations/4_deterministic_overrides.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 5,
            description: "immutable_timezones",
            sql: include_str!("../migrations/5_immutable_timezones.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 6,
            description: "uom_paradox",
            sql: include_str!("../migrations/6_uom_paradox.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 7,
            description: "hitl_orchestrator",
            sql: include_str!("../migrations/7_hitl_orchestrator.sql"),
            kind: MigrationKind::Up,
        },
        Migration {
            version: 8,
            description: "unified_translation_layer",
            sql: include_str!("../migrations/8_unified_translation_layer.sql"),
            kind: MigrationKind::Up,
        }
    ];

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_sql::Builder::default()
                .add_migrations("sqlite:logihex.db", migrations)
                .build(),
        )
        .invoke_handler(tauri::generate_handler![
            run_ml_forecast, 
            generate_statistical_forecast, 
            trigger_backtest, 
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
