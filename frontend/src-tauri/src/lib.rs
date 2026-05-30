pub mod ai;

use tauri_plugin_sql::{Migration, MigrationKind};
use tauri_plugin_shell::ShellExt;
use std::time::Duration;

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
async fn run_ml_forecast(app_handle: tauri::AppHandle, history: String, horizon: u32) -> Result<String, String> {
    let sidecar_command = app_handle.shell().sidecar("forecast")
        .map_err(|e| format!("Failed to create sidecar command: {}", e))?;

    let output = tokio::time::timeout(
        Duration::from_secs(180),
        sidecar_command
            .args(["--history", &history, "--horizon", &horizon.to_string()])
            .output()
    )
    .await
    .map_err(|_| "Sidecar timed out after 180 seconds. The forecast process may be stalled or downloading the model weights.".to_string())?
    .map_err(|e| format!("Failed to execute sidecar: {}", e))?;

    if output.status.success() {
        let result = String::from_utf8(output.stdout).map_err(|e| e.to_string())?;
        Ok(result)
    } else {
        let err = String::from_utf8(output.stderr).map_err(|e| e.to_string())?;
        Err(format!("Sidecar failed: {}", err))
    }
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

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_sql::Builder::default()
                .add_migrations("sqlite:logihex.db", migrations)
                .build(),
        )
        .invoke_handler(tauri::generate_handler![run_ml_forecast, generate_statistical_forecast, trigger_backtest, download_ai_pack])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
