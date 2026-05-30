pub mod writer;

use sqlx::sqlite::{SqliteConnectOptions, SqlitePoolOptions};
use sqlx::SqlitePool;
use std::str::FromStr;
use tauri::Manager;

pub async fn init_db(app_handle: &tauri::AppHandle) -> Result<SqlitePool, String> {
    let mut db_path = app_handle.path().app_data_dir().map_err(|_| "Failed to resolve app data dir".to_string())?;
    db_path.push("logihex.db");
    
    let db_url = format!("sqlite:{}", db_path.to_string_lossy());

    // Configure SQLite for WAL and Fast Concurrent Reads
    let options = SqliteConnectOptions::from_str(&db_url)
        .map_err(|e| e.to_string())?
        .create_if_missing(true)
        .journal_mode(sqlx::sqlite::SqliteJournalMode::Wal)
        .synchronous(sqlx::sqlite::SqliteSynchronous::Normal)
        .foreign_keys(true);

    // Bounded pool size to prevent connection starvation, but allow concurrent reads
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect_with(options)
        .await
        .map_err(|e| format!("Failed to create connection pool: {}", e))?;

    Ok(pool)
}
