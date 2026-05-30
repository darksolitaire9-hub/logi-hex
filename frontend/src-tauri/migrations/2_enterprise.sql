-- 1. Add Role-Based Access Control (Admin PIN)
ALTER TABLE workspaces ADD COLUMN admin_pin_hash TEXT;

-- 2. Enable Soft Deletes for Immutable Ledgers
ALTER TABLE items ADD COLUMN deleted_at DATETIME DEFAULT NULL;
ALTER TABLE clients ADD COLUMN deleted_at DATETIME DEFAULT NULL;

-- 3. Traceability Indices (Fast O(log N) chronological lookups)
CREATE INDEX IF NOT EXISTS idx_movements_timestamp ON movements(timestamp);

-- 4. O(1) Cache Table for Client Balances
CREATE TABLE IF NOT EXISTS client_item_balances (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    balance REAL DEFAULT 0,
    FOREIGN KEY(workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY(client_id) REFERENCES clients(id),
    FOREIGN KEY(item_id) REFERENCES items(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_client_item_balances_unique ON client_item_balances(workspace_id, client_id, item_id);
