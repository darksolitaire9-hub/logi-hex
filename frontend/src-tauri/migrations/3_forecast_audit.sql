CREATE TABLE IF NOT EXISTS forecast_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL, -- e.g. 'TimesFM', 'Nixtla:Naive'
    input_snapshot TEXT NOT NULL, -- JSON array of input data
    base_prediction REAL NOT NULL,
    human_override_percentage REAL DEFAULT 0,
    final_prediction REAL NOT NULL,
    FOREIGN KEY (item_id) REFERENCES items(id)
);
