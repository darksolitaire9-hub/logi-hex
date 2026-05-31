pub mod writer;

use sqlx::sqlite::{SqliteConnectOptions, SqlitePoolOptions};
use sqlx::SqlitePool;
use std::str::FromStr;
use tauri::Manager;

/// Resolves the canonical path to the SQLite database file inside the per-user application data folder.
pub fn resolve_db_path(app_handle: &tauri::AppHandle) -> Result<std::path::PathBuf, String> {
    let mut db_path = app_handle.path().app_data_dir().map_err(|_| "Failed to resolve app data dir".to_string())?;
    db_path.push("logihex.db");
    Ok(db_path)
}

/// Recursively creates the parent directories of the database file if they do not exist.
pub fn create_db_dir(db_path: &std::path::Path) -> Result<(), String> {
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create database directory '{}': {}", parent.display(), e))?;
    }
    Ok(())
}

pub async fn init_db(app_handle: &tauri::AppHandle) -> Result<SqlitePool, String> {
    let db_path = resolve_db_path(app_handle)?;
    
    // Ensure parent directory exists before establishing connection pool
    create_db_dir(&db_path)?;

    // Log the resolved path at startup in debug/info logs
    log::info!("Initializing SQLite database pool at: {}", db_path.display());
    
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

    // Run migrations using local migrations folder
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await
        .map_err(|e| format!("Failed to run database migrations: {}", e))?;

    Ok(pool)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_db_dir_creates_directories() {
        let temp = std::env::temp_dir();
        let nested_dir = temp.join("logihex_test_nested").join("further_nested");
        let db_file_path = nested_dir.join("test_logihex.db");

        // Clean up first if it exists from a previous test run
        if nested_dir.exists() {
            let _ = std::fs::remove_dir_all(&nested_dir);
        }

        assert!(!nested_dir.exists());
        create_db_dir(&db_file_path).unwrap();
        assert!(nested_dir.exists());

        // Clean up
        let _ = std::fs::remove_dir_all(&nested_dir);
    }

    #[test]
    fn test_create_db_dir_handles_existing_directory() {
        let temp = std::env::temp_dir();
        let db_file_path = temp.join("test_logihex.db");

        assert!(temp.exists());
        create_db_dir(&db_file_path).unwrap();
        assert!(temp.exists());
    }
}
