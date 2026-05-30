-- f:\container tracker\logi-hex\frontend\src-tauri\migrations\1_init.sql

CREATE TABLE workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('ACCOUNTS', 'INVENTORY')),
    pin_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clients (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    info TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE items (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    unit TEXT NOT NULL,
    current_stock REAL DEFAULT 0,
    reorder_point REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE movements (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    direction TEXT NOT NULL CHECK (direction IN ('SEND', 'COLLECT', 'RECEIVE', 'USE', 'CORRECT')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    client_id TEXT REFERENCES clients(id) ON DELETE SET NULL,
    correction_reason TEXT CHECK (correction_reason IN ('DAMAGE', 'LOSS', 'COUNT_ADJUSTMENT', 'OTHER')),
    notes TEXT
);

CREATE TABLE movement_line_items (
    id TEXT PRIMARY KEY,
    movement_id TEXT NOT NULL REFERENCES movements(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    quantity REAL NOT NULL CHECK (quantity > 0)
);

CREATE TABLE forecasts (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    horizon_days INTEGER NOT NULL,
    forecast_json TEXT NOT NULL -- Stored as a flat JSON array of predicted numbers
);

-- Indexes for fast querying
CREATE INDEX idx_items_workspace ON items(workspace_id);
CREATE INDEX idx_movements_workspace ON movements(workspace_id);
CREATE INDEX idx_movements_client ON movements(client_id);
CREATE INDEX idx_movement_lines_item ON movement_line_items(item_id);
