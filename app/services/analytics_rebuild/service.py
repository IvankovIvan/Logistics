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

from app.repositories.rebuild_repository import (
    rebuild_snapshot_data,
    truncate_snapshot,
)
from app.services.db.connection import get_analytics_connection


LOGGER = logging.getLogger(__name__)


def _run_rebuild(conn: Connection) -> int:
    truncate_snapshot(conn)
    inserted_rows = rebuild_snapshot_data(conn)

    return inserted_rows


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
