-- f:\container tracker\logi-hex\frontend\src-tauri\migrations\8_unified_translation_layer.sql

-- Add identity constraints for what "Base Stock" actually means. Defaults to 'Pieces' for backwards compatibility.
ALTER TABLE items ADD COLUMN base_unit_name TEXT NOT NULL DEFAULT 'Pieces';

-- Define the single source of truth for the dashboard UI
ALTER TABLE items ADD COLUMN primary_uom_id TEXT REFERENCES item_uoms(id);
