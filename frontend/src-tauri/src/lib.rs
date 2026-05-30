use tauri_plugin_sql::{Migration, MigrationKind};
use tauri_plugin_shell::ShellExt;
use std::time::Duration;

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
        }
    ];

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_sql::Builder::default()
                .add_migrations("sqlite:logihex.db", migrations)
                .build(),
        )
        .invoke_handler(tauri::generate_handler![run_ml_forecast])
        .setup(|app| {
            // Strictly Enforce Enterprise Data Integrity
            tauri::async_runtime::block_on(async {
                if let Ok(db) = tauri_plugin_sql::core::Db::load("sqlite:logihex.db").await {
                    let _ = db.execute("PRAGMA foreign_keys = ON;", vec![]).await;
                }
            });

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
