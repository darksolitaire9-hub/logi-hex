-- Migration 9: Advanced Model Tuning
-- Adds reactivity presets and raw alpha overrides to the forecasting settings.

ALTER TABLE item_forecasting_settings ADD COLUMN reactivity_preset TEXT NOT NULL DEFAULT 'Balanced';
ALTER TABLE item_forecasting_settings ADD COLUMN alpha_override REAL;
