-- f:\container tracker\logi-hex\frontend\src-tauri\migrations\5_immutable_timezones.sql

ALTER TABLE workspaces ADD COLUMN timezone TEXT DEFAULT 'UTC';
ALTER TABLE movements ADD COLUMN local_date TEXT;

-- Update existing movements to have a local_date based on UTC as a fallback
UPDATE movements SET local_date = date(timestamp);
