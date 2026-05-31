use tauri::{State, Emitter};
use sqlx::SqlitePool;
use uuid::Uuid;
use sha2::{Sha256, Digest};
use crate::types::Workspace;

fn hash_pin(pin: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(pin.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}

#[tauri::command]
pub async fn get_workspaces(
    db_pool: State<'_, SqlitePool>
) -> Result<Vec<Workspace>, String> {
    sqlx::query_as::<_, Workspace>("SELECT * FROM workspaces ORDER BY created_at DESC")
        .fetch_all(db_pool.inner())
        .await
        .map_err(|e| format!("Failed to fetch workspaces: {}", e))
}

#[tauri::command]
pub async fn create_workspace(
    app_handle: tauri::AppHandle,
    name: String,
    mode: String,
    pin: String,
    admin_pin: String,
    timezone: String,
    db_pool: State<'_, SqlitePool>
) -> Result<Workspace, String> {
    let new_id = Uuid::new_v4().to_string();
    let pin_hash = hash_pin(&pin);
    let admin_pin_hash = hash_pin(&admin_pin);

    sqlx::query(
        "INSERT INTO workspaces (id, name, mode, pin_hash, admin_pin_hash, timezone) VALUES (?, ?, ?, ?, ?, ?)"
    )
    .bind(&new_id)
    .bind(&name)
    .bind(&mode)
    .bind(&pin_hash)
    .bind(&admin_pin_hash)
    .bind(&timezone)
    .execute(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to insert workspace: {}", e))?;

    // Emit event for UI reactivity (Second Level Thinking)
    let _ = app_handle.emit("db_changed", "workspace");

    // Fetch the newly created workspace to return it
    let created = sqlx::query_as::<_, Workspace>("SELECT * FROM workspaces WHERE id = ?")
        .bind(&new_id)
        .fetch_one(db_pool.inner())
        .await
        .map_err(|e| format!("Failed to fetch newly created workspace: {}", e))?;

    Ok(created)
}
