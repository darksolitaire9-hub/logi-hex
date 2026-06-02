-- Add blind indexing columns to support deterministic search on encrypted fields
-- This is critical for scaling past O(N) JavaScript decryption bottlenecks.

ALTER TABLE items ADD COLUMN label_index TEXT;
CREATE INDEX idx_items_label_index ON items(workspace_id, label_index);

ALTER TABLE clients ADD COLUMN client_name_index TEXT;
CREATE INDEX idx_clients_name_index ON clients(workspace_id, client_name_index);
