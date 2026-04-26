"""
Rebuild service for analytics current snapshot (Project #2 V2).

Инварианты:
- НЕ меняет event store
- полностью пересобирает analytics.current_batch_state из history
- использует одну транзакцию на весь rebuild
"""

from __future__ import annotations

import logging
import time

from psycopg import Connection

from app.services.db.connection import get_analytics_connection


LOGGER = logging.getLogger(__name__)

TRUNCATE_CURRENT_BATCH_STATE = """
TRUNCATE TABLE analytics.current_batch_state;
"""

REBUILD_SNAPSHOT = """
WITH latest_events AS (
    SELECT DISTINCT ON (e.batch_id)
        e.batch_id,
        e.order_id,
        e.sku_id,
        e.warehouse_id,
        e.status_id,
        e.quantity,
        e.source_location_id,
        e.destination_location_id,
        e.event_time,
        e.status_reason_id,
        e.event_id
    FROM analytics.inventory_status_events e
    ORDER BY e.batch_id, e.event_time DESC, e.event_id DESC
),
filtered AS (
    SELECT
        le.batch_id,
        le.order_id,
        le.sku_id,
        le.warehouse_id,
        le.status_id,
        le.quantity,
        le.source_location_id,
        le.destination_location_id,
        le.event_time
    FROM latest_events le
    JOIN analytics.status_reason sr
        ON sr.status_reason_id = le.status_reason_id
    WHERE sr.is_tracking_finished = false
)
INSERT INTO analytics.current_batch_state (
    batch_id,
    order_id,
    sku_id,
    warehouse_id,
    status_id,
    quantity,
    source_location_id,
    destination_location_id,
    last_event_time
)
SELECT
    f.batch_id,
    f.order_id,
    f.sku_id,
    f.warehouse_id,
    f.status_id,
    f.quantity,
    f.source_location_id,
    f.destination_location_id,
    f.event_time
FROM filtered f;
"""


def _run_rebuild(conn: Connection) -> int:
    with conn.cursor() as cur:
        cur.execute(TRUNCATE_CURRENT_BATCH_STATE)
        cur.execute(REBUILD_SNAPSHOT)
        inserted_rows = cur.rowcount if cur.rowcount is not None else 0

    return int(inserted_rows)


def rebuild_snapshot(conn: Connection | None = None) -> int:
    """
    Полностью пересобирает analytics.current_batch_state из event history.

    Шаги:
    1. BEGIN (через conn)
    2. TRUNCATE analytics.current_batch_state
    3. INSERT latest non-final batches (CTE latest_events + filtered)
    4. COMMIT

    Возвращает количество вставленных строк.
    """

    started_at = time.perf_counter()

    if conn is not None:
        inserted_rows = _run_rebuild(conn)
    else:
        with get_analytics_connection() as owned_conn:
            try:
                inserted_rows = _run_rebuild(owned_conn)
                owned_conn.commit()
            except Exception:
                owned_conn.rollback()
                raise

    elapsed_ms = (time.perf_counter() - started_at) * 1000.0
    LOGGER.info(
        "analytics snapshot rebuild completed: inserted_rows=%s elapsed_ms=%.2f",
        inserted_rows,
        elapsed_ms,
    )

    return int(inserted_rows)
