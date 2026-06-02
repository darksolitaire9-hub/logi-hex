use tauri::{State, Emitter};
use sqlx::SqlitePool;
use uuid::Uuid;
use crate::types::{ItemRow, ItemUomRow, AlternateUomPayload};
use crate::crypto::{self, state::CryptoState};

#[tauri::command]
pub async fn get_items(
    workspace_id: String,
    search_term: Option<String>,
    cursor: Option<String>,
    limit: Option<i64>,
    db_pool: State<'_, SqlitePool>,
    crypto_state: State<'_, CryptoState>
) -> Result<(Vec<ItemRow>, Vec<ItemUomRow>), String> {
    let key = crypto_state.key();
    let query_limit = limit.unwrap_or(100);

    let mut query_str = String::from(
        "SELECT * FROM items 
         WHERE workspace_id = ? AND deleted_at IS NULL"
    );

    let mut search_hash = None;
    if let Some(ref term) = search_term {
        if !term.is_empty() {
            let hash = crypto::hash_blind_index(term, key)?;
            query_str.push_str(" AND label_index = ?");
            search_hash = Some(hash);
        }
    }

    if cursor.is_some() {
        query_str.push_str(" AND created_at < ?");
    }

    query_str.push_str(" ORDER BY created_at DESC LIMIT ?");

    // Dynamic binding
    let mut query = sqlx::query_as::<_, ItemRow>(&query_str).bind(&workspace_id);

    if let Some(hash) = &search_hash {
        query = query.bind(hash);
    }
    if let Some(ref c) = cursor {
        query = query.bind(c);
    }
    query = query.bind(query_limit);

    let mut items = query.fetch_all(db_pool.inner()).await
        .map_err(|e| format!("Failed to fetch items: {}", e))?;

    // Decrypt labels in Rust
    for item in &mut items {
        if !item.label.is_empty() {
            item.label = crypto::decrypt_field(&item.label, key).unwrap_or_else(|_| item.label.clone());
        }
    }

    let mut uoms = Vec::new();
    if !items.is_empty() {
        let item_ids: Vec<String> = items.iter().map(|i| i.id.clone()).collect();
        let placeholders = vec!["?"; item_ids.len()].join(",");
        let uom_query_str = format!("SELECT * FROM item_uoms WHERE item_id IN ({})", placeholders);
        
        let mut uom_query = sqlx::query_as::<_, ItemUomRow>(&uom_query_str);
        for id in &item_ids {
            uom_query = uom_query.bind(id);
        }
        
        uoms = uom_query.fetch_all(db_pool.inner()).await
            .map_err(|e| format!("Failed to fetch UOMs: {}", e))?;
    }

    Ok((items, uoms))
}

#[tauri::command]
pub async fn create_item(
    app_handle: tauri::AppHandle,
    workspace_id: String,
    label: String, // PLAINTEXT from frontend
    base_unit_name: String,
    reorder_point: Option<f64>,
    alternate_uoms: Vec<AlternateUomPayload>,
    primary_uom_name: Option<String>,
    db_pool: State<'_, SqlitePool>,
    crypto_state: State<'_, CryptoState>
) -> Result<String, String> {
    let key = crypto_state.key();
    let encrypted_label = crypto::encrypt_field(&label, key)?;
    let label_index = crypto::hash_blind_index(&label, key)?;

    let pool = db_pool.inner();
    let mut tx = pool.begin().await
        .map_err(|e| format!("Failed to begin transaction: {}", e))?;

    let item_id = Uuid::new_v4().to_string();

    // Step 1: Insert item with base identity
    sqlx::query(
        "INSERT INTO items (id, workspace_id, label, label_index, unit, reorder_point, base_unit_name) 
         VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    .bind(&item_id)
    .bind(&workspace_id)
    .bind(&encrypted_label)
    .bind(&label_index)
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
    label: String, // PLAINTEXT
    unit: String,
    db_pool: State<'_, SqlitePool>,
    crypto_state: State<'_, CryptoState>
) -> Result<(), String> {
    let key = crypto_state.key();
    let encrypted_label = crypto::encrypt_field(&label, key)?;
    let label_index = crypto::hash_blind_index(&label, key)?;

    sqlx::query(
        "UPDATE items SET label = ?, label_index = ?, unit = ? WHERE id = ? AND workspace_id = ?"
    )
    .bind(&encrypted_label)
    .bind(&label_index)
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
pub async fn fetch_items_count(
    workspace_id: String,
    db_pool: State<'_, SqlitePool>,
) -> Result<i64, String> {
    let row: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM items WHERE workspace_id = ? AND deleted_at IS NULL")
        .bind(&workspace_id)
        .fetch_one(db_pool.inner())
        .await
        .map_err(|e| format!("DB error: {}", e))?;
    
    Ok(row.0)
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
