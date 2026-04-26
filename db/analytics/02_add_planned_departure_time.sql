-- -----------------------------------------------------
-- Project 11: planned_departure_time columns
-- -----------------------------------------------------

ALTER TABLE analytics.inventory_status_events
    ADD COLUMN IF NOT EXISTS planned_departure_time TIMESTAMPTZ NULL;

ALTER TABLE analytics.current_batch_state
    ADD COLUMN IF NOT EXISTS planned_departure_time TIMESTAMPTZ NULL;
