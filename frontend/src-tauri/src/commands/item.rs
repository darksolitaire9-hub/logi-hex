use tauri::{State, Emitter};
use sqlx::SqlitePool;
use uuid::Uuid;
use crate::types::{ItemRow, ItemUomRow, AlternateUomPayload};

#[tauri::command]
pub async fn get_items(
    workspace_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<(Vec<ItemRow>, Vec<ItemUomRow>), String> {
    let items = sqlx::query_as::<_, ItemRow>(
        "SELECT * FROM items 
         WHERE workspace_id = ? 
         ORDER BY 
           CASE WHEN deleted_at IS NULL THEN 0 ELSE 1 END ASC,
           created_at DESC"
    )
    .bind(&workspace_id)
    .fetch_all(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to fetch items: {}", e))?;

    let uoms = sqlx::query_as::<_, ItemUomRow>(
        "SELECT * FROM item_uoms WHERE item_id IN (SELECT id FROM items WHERE workspace_id = ?)"
    )
    .bind(&workspace_id)
    .fetch_all(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to fetch UOMs: {}", e))?;

    Ok((items, uoms))
}

#[tauri::command]
pub async fn create_item(
    app_handle: tauri::AppHandle,
    workspace_id: String,
    label: String, // encrypted from frontend
    base_unit_name: String,
    reorder_point: Option<f64>,
    alternate_uoms: Vec<AlternateUomPayload>,
    primary_uom_name: Option<String>,
    db_pool: State<'_, SqlitePool>
) -> Result<String, String> {
    let pool = db_pool.inner();
    let mut tx = pool.begin().await
        .map_err(|e| format!("Failed to begin transaction: {}", e))?;

    let item_id = Uuid::new_v4().to_string();

    // Step 1: Insert item with base identity
    sqlx::query(
        "INSERT INTO items (id, workspace_id, label, unit, reorder_point, base_unit_name) 
         VALUES (?, ?, ?, ?, ?, ?)"
    )
    .bind(&item_id)
    .bind(&workspace_id)
    .bind(&label)
    .bind(&base_unit_name)
    .bind(reorder_point)
    .bind(&base_unit_name)
    .execute(&mut *tx)
    .await
    .map_err(|e| format!("Failed to insert item: {}", e))?;

    // Step 2: Insert 1.0 Base UOM explicitly to solve the Identity Flaw
    let base_uom_id = Uuid::new_v4().to_string();
    sqlx::query(
        "INSERT INTO item_uoms (id, item_id, unit_name, multiplier) 
         VALUES (?, ?, ?, 1.0)"
    )
    .bind(&base_uom_id)
    .bind(&item_id)
    .bind(&base_unit_name)
    .execute(&mut *tx)
    .await
    .map_err(|e| format!("Failed to insert base UOM: {}", e))?;

    // Step 3: Insert alternates
    let mut primary_id_to_set = base_uom_id.clone();
    for uom in alternate_uoms {
        let uom_id = Uuid::new_v4().to_string();
        sqlx::query(
            "INSERT INTO item_uoms (id, item_id, unit_name, multiplier) 
             VALUES (?, ?, ?, ?)"
        )
        .bind(&uom_id)
        .bind(&item_id)
        .bind(&uom.unit_name)
        .bind(uom.multiplier)
        .execute(&mut *tx)
        .await
        .map_err(|e| format!("Failed to insert alternate UOM '{}': {}", uom.unit_name, e))?;

        if let Some(ref primary_name) = primary_uom_name {
            if primary_name == &uom.unit_name {
                primary_id_to_set = uom_id;
            }
        }
    }

    // Step 4: Set the Primary UOM
    sqlx::query("UPDATE items SET primary_uom_id = ? WHERE id = ?")
        .bind(&primary_id_to_set)
        .bind(&item_id)
        .execute(&mut *tx)
        .await
        .map_err(|e| format!("Failed to update primary UOM: {}", e))?;

    tx.commit().await
        .map_err(|e| format!("Transaction commit failed: {}", e))?;

    let _ = app_handle.emit("db_changed", "item");

    Ok(item_id)
}

#[tauri::command]
pub async fn update_item(
    app_handle: tauri::AppHandle,
    id: String,
    workspace_id: String,
    label: String,
    unit: String,
    db_pool: State<'_, SqlitePool>
) -> Result<(), String> {
    sqlx::query(
        "UPDATE items SET label = ?, unit = ? WHERE id = ? AND workspace_id = ?"
    )
    .bind(&label)
    .bind(&unit)
    .bind(&id)
    .bind(&workspace_id)
    .execute(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to update item: {}", e))?;

    let _ = app_handle.emit("db_changed", "item");

    Ok(())
}

#[tauri::command]
pub async fn delete_item(
    app_handle: tauri::AppHandle,
    id: String,
    workspace_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<(), String> {
    sqlx::query(
        "UPDATE items SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND workspace_id = ?"
    )
    .bind(&id)
    .bind(&workspace_id)
    .execute(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to delete item: {}", e))?;

    let _ = app_handle.emit("db_changed", "item");

    Ok(())
}

#[tauri::command]
pub async fn get_low_stock_items(
    workspace_id: String,
    db_pool: State<'_, SqlitePool>
) -> Result<Vec<ItemRow>, String> {
    sqlx::query_as::<_, ItemRow>(
        "SELECT * FROM items 
         WHERE workspace_id = ? 
           AND deleted_at IS NULL 
           AND reorder_point IS NOT NULL 
           AND current_stock <= reorder_point
         ORDER BY current_stock ASC"
    )
    .bind(&workspace_id)
    .fetch_all(db_pool.inner())
    .await
    .map_err(|e| format!("Failed to fetch low stock items: {}", e))
}
