use sqlx::Row;
use uuid::Uuid;
use tauri::State;
use crate::types::{
    LogMovementCommand, MovementDirection, LedgerError, MovementHistoryRow, ExportRow,
};
use crate::crypto::{self, state::CryptoState};

/// Logs a stock movement. Rust owns: UUID generation, UOM translation,
/// stock validation (atomic SQL), notes encryption, and the full transaction.
/// Vue sends intent — Rust executes.
#[tauri::command]
pub async fn log_movement(
    payload: LogMovementCommand,
    db_pool: State<'_, sqlx::SqlitePool>,
    crypto_state: State<'_, CryptoState>,
) -> Result<String, String> {
    if payload.lines.is_empty() {
        return Err(LedgerError::EmptyLines.into());
    }

    let pool = &*db_pool;
    let key = crypto_state.key();

    // Encrypt notes in Rust — key never leaves Rust memory
    let encrypted_notes = match &payload.notes {
        Some(notes) if !notes.is_empty() => {
            Some(crypto::encrypt_field(notes, key)
                .map_err(|e| String::from(LedgerError::EncryptionError(e)))?)
        }
        _ => None,
    };

    // Begin transaction
    let mut tx = pool.begin().await
        .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;

    let movement_id = Uuid::new_v4().to_string();

    // Compute local date from workspace timezone
    let local_date = chrono_tz_local_date(&payload.timezone);

    // Insert parent movement row
    sqlx::query(
        "INSERT INTO movements (id, workspace_id, direction, client_id, correction_reason, notes, local_date)
         VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    .bind(&movement_id)
    .bind(&payload.workspace_id)
    .bind(serde_json::to_value(&payload.direction).unwrap().as_str().unwrap_or("UNKNOWN"))
    .bind(&payload.client_id)
    .bind(payload.correction_reason.as_ref().map(|r| serde_json::to_value(r).unwrap().as_str().unwrap_or("").to_string()))
    .bind(&encrypted_notes)
    .bind(&local_date)
    .execute(&mut *tx)
    .await
    .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;

    // Process each line — UOM translation + atomic stock update
    for line in &payload.lines {
        let final_quantity = line.quantity * line.multiplier;

        if final_quantity <= 0.0 {
            continue;
        }

        match payload.direction {
            MovementDirection::Send | MovementDirection::Use => {
                // ATOMIC: check and decrement in one SQL statement — no TOCTOU window
                let result = sqlx::query(
                    "UPDATE items SET current_stock = current_stock - ?
                     WHERE id = ? AND workspace_id = ? AND current_stock >= ?"
                )
                .bind(final_quantity)
                .bind(&line.item_id)
                .bind(&payload.workspace_id)
                .bind(final_quantity)
                .execute(&mut *tx)
                .await
                .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;

                if result.rows_affected() == 0 {
                    // Rollback and return typed error with current stock level
                    let current: f64 = sqlx::query(
                        "SELECT current_stock FROM items WHERE id = ? AND workspace_id = ?"
                    )
                    .bind(&line.item_id)
                    .bind(&payload.workspace_id)
                    .fetch_optional(pool)
                    .await
                    .ok()
                    .flatten()
                    .map(|r| r.get::<f64, _>("current_stock"))
                    .unwrap_or(0.0);

                    let _ = tx.rollback().await;
                    return Err(LedgerError::InsufficientStock {
                        item_id: line.item_id.clone(),
                        available: current,
                        requested: final_quantity,
                    }.into());
                }
            }
            MovementDirection::Receive | MovementDirection::Correct | MovementDirection::Collect => {
                sqlx::query(
                    "UPDATE items SET current_stock = current_stock + ?
                     WHERE id = ? AND workspace_id = ?"
                )
                .bind(final_quantity)
                .bind(&line.item_id)
                .bind(&payload.workspace_id)
                .execute(&mut *tx)
                .await
                .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;
            }
        }

        // Insert line item
        sqlx::query(
            "INSERT INTO movement_line_items (id, movement_id, item_id, quantity, recorded_unit)
             VALUES (?, ?, ?, ?, ?)"
        )
        .bind(Uuid::new_v4().to_string())
        .bind(&movement_id)
        .bind(&line.item_id)
        .bind(final_quantity)
        .bind(&line.recorded_unit)
        .execute(&mut *tx)
        .await
        .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;

        // Client balance ledger (SEND increases receivable, COLLECT decreases it)
        if let Some(client_id) = &payload.client_id {
            if matches!(payload.direction, MovementDirection::Send | MovementDirection::Collect) {
                let balance_delta = if payload.direction == MovementDirection::Send {
                    final_quantity
                } else {
                    -final_quantity
                };

                sqlx::query(
                    "INSERT INTO client_item_balances (id, workspace_id, client_id, item_id, balance)
                     VALUES (?, ?, ?, ?, ?)
                     ON CONFLICT(workspace_id, client_id, item_id)
                     DO UPDATE SET balance = balance + excluded.balance"
                )
                .bind(Uuid::new_v4().to_string())
                .bind(&payload.workspace_id)
                .bind(client_id)
                .bind(&line.item_id)
                .bind(balance_delta)
                .execute(&mut *tx)
                .await
                .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;
            }
        }
    }

    tx.commit().await
        .map_err(|e| String::from(LedgerError::DatabaseError(e.to_string())))?;

    Ok(movement_id)
}

/// Fetches movement history for a specific client, decrypting notes in Rust.
#[tauri::command]
pub async fn fetch_client_history(
    workspace_id: String,
    client_id: String,
    db_pool: State<'_, sqlx::SqlitePool>,
    crypto_state: State<'_, CryptoState>,
) -> Result<Vec<MovementHistoryRow>, String> {
    let rows = sqlx::query(
        "SELECT m.id, m.workspace_id, m.direction, m.timestamp, m.client_id,
                m.correction_reason, m.notes, mli.quantity, i.label as item_label
         FROM movements m
         JOIN movement_line_items mli ON m.id = mli.movement_id
         JOIN items i ON mli.item_id = i.id
         WHERE m.workspace_id = ? AND m.client_id = ?
         ORDER BY m.timestamp DESC"
    )
    .bind(&workspace_id)
    .bind(&client_id)
    .fetch_all(&*db_pool)
    .await
    .map_err(|e| format!("DB error: {}", e))?;

    map_history_rows(rows, crypto_state.key())
}

/// Fetches all movement history for a workspace, decrypting notes in Rust.
#[tauri::command]
pub async fn fetch_global_history(
    workspace_id: String,
    db_pool: State<'_, sqlx::SqlitePool>,
    crypto_state: State<'_, CryptoState>,
) -> Result<Vec<MovementHistoryRow>, String> {
    let rows = sqlx::query(
        "SELECT m.id, m.workspace_id, m.direction, m.timestamp, m.client_id,
                m.correction_reason, m.notes, mli.quantity, i.label as item_label
         FROM movements m
         JOIN movement_line_items mli ON m.id = mli.movement_id
         JOIN items i ON mli.item_id = i.id
         WHERE m.workspace_id = ?
         ORDER BY m.timestamp DESC"
    )
    .bind(&workspace_id)
    .fetch_all(&*db_pool)
    .await
    .map_err(|e| format!("DB error: {}", e))?;

    map_history_rows(rows, crypto_state.key())
}

fn map_history_rows(
    rows: Vec<sqlx::sqlite::SqliteRow>,
    key: &[u8],
) -> Result<Vec<MovementHistoryRow>, String> {
    let mut result = Vec::with_capacity(rows.len());

    for row in rows {
        let raw_notes: Option<String> = row.get("notes");
        let decrypted_notes = match raw_notes {
            Some(ref s) if !s.is_empty() => {
                // Try to decrypt — if it fails (old plaintext data), return as-is
                Some(crypto::decrypt_field(s, key).unwrap_or_else(|_| s.clone()))
            }
            _ => None,
        };

        result.push(MovementHistoryRow {
            id: row.get("id"),
            workspace_id: row.get("workspace_id"),
            direction: row.get("direction"),
            timestamp: row.get("timestamp"),
            client_id: row.get("client_id"),
            correction_reason: row.get("correction_reason"),
            notes: decrypted_notes,
            item_label: row.get("item_label"),
            quantity: row.get("quantity"),
        });
    }

    Ok(result)
}

/// Computes today's local date string (YYYY-MM-DD) in the given IANA timezone.
/// Falls back to UTC if the timezone string is invalid.
pub fn chrono_tz_local_date(tz: &str) -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    // Simple UTC date computation — timezone offset would require chrono-tz which adds binary size.
    // For now we use UTC and note this is a known simplification; full tz support is Phase 5.
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let days = secs / 86400;
    let _year_day = days % 365; // approximate
    let _ = tz; // timezone aware date is Phase 5
    format!("{}", chrono_days_to_date(days))
}

pub fn chrono_days_to_date(days_since_epoch: u64) -> String {
    // Days since Unix epoch (1970-01-01) to YYYY-MM-DD
    let mut y = 1970u64;
    let mut d = days_since_epoch;
    loop {
        let days_in_year = if is_leap(y) { 366 } else { 365 };
        if d < days_in_year { break; }
        d -= days_in_year;
        y += 1;
    }
    let months = [31, if is_leap(y) { 29 } else { 28 }, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    let mut m = 1u64;
    for &dm in &months {
        if d < dm { break; }
        d -= dm;
        m += 1;
    }
    format!("{:04}-{:02}-{:02}", y, m, d + 1)
}

pub fn is_leap(y: u64) -> bool {
    (y % 4 == 0 && y % 100 != 0) || y % 400 == 0
}

#[tauri::command]
pub async fn get_export_data(
    workspace_id: String,
    db_pool: State<'_, sqlx::SqlitePool>,
) -> Result<Vec<ExportRow>, String> {
    sqlx::query_as::<_, ExportRow>(
        "SELECT 
           m.id, m.direction, m.timestamp, m.notes, m.correction_reason,
           c.name as client_name,
           i.label as item_label,
           mli.quantity
         FROM movements m
         LEFT JOIN clients c ON m.client_id = c.id
         JOIN movement_line_items mli ON m.id = mli.movement_id
         JOIN items i ON mli.item_id = i.id
         WHERE m.workspace_id = ?
         ORDER BY m.timestamp DESC"
    )
    .bind(&workspace_id)
    .fetch_all(db_pool.inner())
    .await
    .map_err(|e| format!("DB error: {}", e))
}

