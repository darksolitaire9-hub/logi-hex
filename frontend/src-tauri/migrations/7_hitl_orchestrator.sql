-- Migration 7: Human-in-the-Loop Forecasting Orchestrator

-- Table to store user preferences and overrides for forecasting engines per item.
CREATE TABLE item_forecasting_settings (
    item_id TEXT NOT NULL,
    selected_engine TEXT NOT NULL DEFAULT 'AUTO', -- 'AUTO', 'RUST_CROSTON', 'ONNX_TIMESFM'
    locked BOOLEAN NOT NULL DEFAULT 0, -- If true, the Orchestrator will not auto-switch engines even if another scores better
    last_backtest_date DATETIME,
    PRIMARY KEY (item_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- Table to store the historical backtest scores for each engine, evaluated at specific horizon windows.
-- The Composite Primary Key (item_id, engine_name, horizon_days) natively prevents storage bloat.
-- Running a backtest UPSERTS this table, so we always only have the latest score per configuration.
CREATE TABLE engine_backtest_scores (
    item_id TEXT NOT NULL,
    engine_name TEXT NOT NULL,
    horizon_days INTEGER NOT NULL,
    wape REAL, -- Weighted Absolute Percentage Error (NULL if actuals sum to 0)
    mase REAL, -- Mean Absolute Scaled Error (NULL if training naive error is 0)
    bias REAL, -- Tracking systematic over/under forecasting (NULL if actuals sum to 0)
    last_tested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (item_id, engine_name, horizon_days),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
