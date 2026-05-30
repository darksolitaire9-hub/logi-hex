ALTER TABLE forecast_audit_logs ADD COLUMN human_adjustment_qty REAL DEFAULT 0;
ALTER TABLE forecast_audit_logs ADD COLUMN override_reason TEXT;
