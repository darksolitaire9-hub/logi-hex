use tauri::{State, Emitter};
use sqlx::SqlitePool;
use uuid::Uuid;
use crate::types::{ClientRow, ClientBalanceRow};

#[tauri::command]
pub async fn get_clients(
    workspace_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<Vec<ClientRow>, String> {
    sqlx::query_as::<_, ClientRow>(
        "SELECT 
           c.id,
           c.workspace_id,
           c.name,
           c.info,
           c.created_at,
           c.deleted_at,
           COALESCE(SUM(b.balance), 0.0) as total_items_held
         FROM clients c
         LEFT JOIN client_item_balances b ON c.id = b.client_id
         WHERE c.workspace_id = ?
         GROUP BY c.id
         ORDER BY 
           CASE WHEN c.deleted_at IS NULL THEN 0 ELSE 1 END ASC,
           c.created_at DESC"
    )
    .bind(&workspace_id)
    .fetch_all(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to fetch clients: {}", e))
}

#[tauri::command]
pub async fn create_client(
    app_handle: tauri::AppHandle,
    workspace_id: String,
    name: String, // encrypted name from frontend
    info: Option<String>, // encrypted info from frontend
    db_pool: State<'_, SqlitePool>
) -> Result<String, String> {
    let new_id = Uuid::new_v4().to_string();

    sqlx::query(
        "INSERT INTO clients (id, workspace_id, name, info) VALUES (?, ?, ?, ?)"
    )
    .bind(&new_id)
    .bind(&workspace_id)
    .bind(&name)
    .bind(&info)
    .execute(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to insert client: {}", e))?;

    let _ = app_handle.emit("db_changed", "client");

    Ok(new_id)
}

#[tauri::command]
pub async fn delete_client(
    app_handle: tauri::AppHandle,
    id: String,
    workspace_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<(), String> {
    sqlx::query(
        "UPDATE clients SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND workspace_id = ?"
    )
    .bind(&id)
    .bind(&workspace_id)
    .execute(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to delete client: {}", e))?;

    let _ = app_handle.emit("db_changed", "client");

    Ok(())
}

#[tauri::command]
pub async fn get_client(
    id: String,
    workspace_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<ClientRow, String> {
    sqlx::query_as::<_, ClientRow>(
        "SELECT 
           c.id,
           c.workspace_id,
           c.name,
           c.info,
           c.created_at,
           c.deleted_at,
           COALESCE(SUM(b.balance), 0.0) as total_items_held
         FROM clients c
         LEFT JOIN client_item_balances b ON c.id = b.client_id
         WHERE c.id = ? AND c.workspace_id = ?
         GROUP BY c.id"
    )
    .bind(&id)
    .bind(&workspace_id)
    .fetch_one(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to fetch client: {}", e))
}

#[tauri::command]
pub async fn get_client_balances(
    client_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<Vec<ClientBalanceRow>, String> {
    sqlx::query_as::<_, ClientBalanceRow>(
        "SELECT 
           i.id as item_id,
           i.label,
           i.unit,
           SUM(
             CASE 
               WHEN m.direction = 'SEND' THEN mli.quantity
               WHEN m.direction = 'COLLECT' THEN -mli.quantity
               ELSE 0.0
             END
           ) as balance
         FROM items i
         JOIN movement_line_items mli ON i.id = mli.item_id
         JOIN movements m ON mli.movement_id = m.id
         WHERE m.client_id = ?
         GROUP BY i.id
         HAVING balance > 0.0
         ORDER BY i.created_at ASC"
    )
    .bind(&client_id)
    .fetch_all(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to fetch client balances: {}", e))
}
