-- =====================================================
-- Project #1.1 — Initial database schema
-- Current-state storage + ingest idempotency
-- =====================================================

-- -----------------------------------------------------
-- 0) Extensions
-- -----------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;

-- -----------------------------------------------------
-- 1) Ingest events (idempotency guard)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ingest_events (
    event_id        TEXT PRIMARY KEY,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    event_time      TIMESTAMPTZ NOT NULL,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------
-- 2) Warehouses — current state
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouses_current (
    id               TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    status           TEXT NOT NULL,

    location         geometry(Point, 4326) NOT NULL,
    quantity         BIGINT NOT NULL,

    last_event_time  TIMESTAMPTZ NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_warehouses_location
    ON warehouses_current
    USING GIST (location);

-- -----------------------------------------------------
-- 3) Shipments — current state
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS shipments_current (
    id               TEXT PRIMARY KEY,

    from_node        TEXT NOT NULL,
    to_node          TEXT NOT NULL,

    status           TEXT NOT NULL,

    last_event_time  TIMESTAMPTZ NOT NULL,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_shipments_from
        FOREIGN KEY (from_node)
        REFERENCES warehouses_current(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_shipments_to
        FOREIGN KEY (to_node)
        REFERENCES warehouses_current(id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_shipments_from_node
    ON shipments_current(from_node);

CREATE INDEX IF NOT EXISTS idx_shipments_to_node
    ON shipments_current(to_node);

CREATE INDEX IF NOT EXISTS idx_shipments_status
    ON shipments_current(status);
