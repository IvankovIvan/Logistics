ALTER TABLE warehouses_current
ADD COLUMN quantity BIGINT NOT NULL;

-- Backfill via ingest events: current-state values must be set by replaying
-- warehouse events with quantity. This migration intentionally does not
-- default or backfill from other sources.
