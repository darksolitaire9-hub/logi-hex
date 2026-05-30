use serde::{Deserialize, Serialize};
use ts_rs::TS;

/// Direction of a stock movement — mirrors the SQL CHECK constraint exactly.
#[derive(Debug, Serialize, Deserialize, TS, Clone, PartialEq)]
#[ts(export, export_to = "../../app/types/generated/")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum MovementDirection {
    Send,
    Collect,
    Receive,
    Use,
    Correct,
}

/// Reason for a correction movement.
#[derive(Debug, Serialize, Deserialize, TS, Clone)]
#[ts(export, export_to = "../../app/types/generated/")]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum CorrectionReason {
    Damage,
    Loss,
    CountAdjustment,
    Other,
}

/// A single line item within a movement — one item, one quantity.
#[derive(Debug, Serialize, Deserialize, TS, Clone)]
#[ts(export, export_to = "../../app/types/generated/")]
pub struct MovementLine {
    pub item_id: String,
    /// Quantity in the recorded unit (before UOM translation).
    pub quantity: f64,
    /// UOM multiplier to translate to base unit. Defaults to 1.0.
    #[serde(default = "default_multiplier")]
    pub multiplier: f64,
    pub recorded_unit: Option<String>,
}

fn default_multiplier() -> f64 { 1.0 }

/// The command payload Vue sends to Rust to log a movement.
/// Rust owns UUID generation, UOM translation, encryption, and all SQL writes.
#[derive(Debug, Serialize, Deserialize, TS)]
#[ts(export, export_to = "../../app/types/generated/")]
pub struct LogMovementCommand {
    pub workspace_id: String,
    pub direction: MovementDirection,
    pub client_id: Option<String>,
    pub correction_reason: Option<CorrectionReason>,
    /// Plaintext from Vue — Rust encrypts before storage.
    pub notes: Option<String>,
    pub lines: Vec<MovementLine>,
    /// IANA timezone string for local_date computation.
    pub timezone: String,
}

/// Typed error enum returned to Vue — never raw strings.
#[derive(Debug, Serialize, TS)]
#[ts(export, export_to = "../../app/types/generated/")]
#[serde(tag = "code", content = "detail")]
pub enum LedgerError {
    InsufficientStock { item_id: String, available: f64, requested: f64 },
    EmptyLines,
    DatabaseError(String),
    EncryptionError(String),
}

impl std::fmt::Display for LedgerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

// Make LedgerError serialisable through the Tauri command boundary
impl From<LedgerError> for String {
    fn from(e: LedgerError) -> String {
        serde_json::to_string(&e).unwrap_or_else(|_| "LedgerError".to_string())
    }
}

/// Payload Vue sends to log a forecast run with human override details.
#[derive(Debug, Serialize, Deserialize, TS)]
#[ts(export, export_to = "../../app/types/generated/")]
pub struct ForecastAuditCommand {
    pub item_id: String,
    pub model_used: String,
    pub input_snapshot: String,
    pub base_prediction: f64,
    pub human_override_percentage: f64,
    pub human_adjustment_qty: f64,
    pub override_reason: String,
    pub final_prediction: f64,
}

/// A decrypted movement history row — what Vue receives from fetch_*_history commands.
#[derive(Debug, Serialize, TS)]
#[ts(export, export_to = "../../app/types/generated/")]
pub struct MovementHistoryRow {
    pub id: String,
    pub workspace_id: String,
    pub direction: String,
    pub timestamp: Option<String>,
    pub client_id: Option<String>,
    pub correction_reason: Option<String>,
    /// Decrypted notes — Rust decrypts before sending to Vue.
    pub notes: Option<String>,
    pub item_label: String,
    pub quantity: f64,
}

/// Structured response containing forecast values and the engine used.
#[derive(Debug, Serialize, TS)]
#[ts(export, export_to = "../../app/types/generated/")]
pub struct ForecastResponse {
    pub forecast: Vec<f64>,
    pub engine_name: String,
}
