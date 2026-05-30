-- f:\container tracker\logi-hex\frontend\src-tauri\migrations\6_uom_paradox.sql

CREATE TABLE item_uoms (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    unit_name TEXT NOT NULL,
    multiplier REAL NOT NULL CHECK (multiplier > 0),
    UNIQUE(item_id, unit_name)
);

-- Keep a historical record of what the human operator actually typed
ALTER TABLE movement_line_items ADD COLUMN recorded_unit TEXT;
