"""
Consistency check for analytics snapshot (worker vs rebuild).

Проверяет, что текущий snapshot совпадает с результатом полного rebuild.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from app.services.analytics_ingest.connection import get_analytics_connection
from app.services.analytics_rebuild.service import rebuild_snapshot


LOGGER = logging.getLogger(__name__)

CREATE_TEMP_SNAPSHOT_BEFORE = """
CREATE TEMP TABLE snapshot_before AS
SELECT
    batch_id,
    order_id,
    sku_id,
    warehouse_id,
    status_id,
    quantity,
    source_location_id,
    destination_location_id,
    last_event_time
FROM analytics.current_batch_state;
"""

COUNT_MISSING_AFTER_REBUILD = """
SELECT COUNT(*) AS cnt
FROM (
    SELECT
        batch_id,
        order_id,
        sku_id,
        warehouse_id,
        status_id,
        quantity,
        source_location_id,
        destination_location_id,
        last_event_time
    FROM snapshot_before
    EXCEPT
    SELECT
        batch_id,
        order_id,
        sku_id,
        warehouse_id,
        status_id,
        quantity,
        source_location_id,
        destination_location_id,
        last_event_time
    FROM analytics.current_batch_state
) AS diff;
"""

COUNT_NEW_AFTER_REBUILD = """
SELECT COUNT(*) AS cnt
FROM (
    SELECT
        batch_id,
        order_id,
        sku_id,
        warehouse_id,
        status_id,
        quantity,
        source_location_id,
        destination_location_id,
        last_event_time
    FROM analytics.current_batch_state
    EXCEPT
    SELECT
        batch_id,
        order_id,
        sku_id,
        warehouse_id,
        status_id,
        quantity,
        source_location_id,
        destination_location_id,
        last_event_time
    FROM snapshot_before
) AS diff;
"""


def _get_count(row) -> int:
    """
    Универсально достаёт COUNT(*) из row:
    - dict_row → row["cnt"]
    - tuple → row[0]
    """
    if row is None:
        raise RuntimeError("COUNT query returned no rows")

    if isinstance(row, Mapping):
        return int(row["cnt"])

    return int(row[0])


def check_snapshot_consistency() -> None:
    """
    Проверяет консистентность snapshot:
    1) сохраняет текущий snapshot в TEMP TABLE snapshot_before
    2) запускает rebuild_snapshot()
    3) сравнивает снимки через два EXCEPT запроса
    4) при расхождениях логирует счётчики и выбрасывает исключение
    5) при совпадении логирует успешную проверку
    """

    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            # 1. сохраняем текущий snapshot
            cur.execute(CREATE_TEMP_SNAPSHOT_BEFORE)
            conn.commit()

            # 2. rebuild внутри той же транзакции
            rebuild_snapshot(conn)

            # 3. считаем расхождения
            cur.execute(COUNT_MISSING_AFTER_REBUILD)
            missing_after_rebuild = _get_count(cur.fetchone())

            cur.execute(COUNT_NEW_AFTER_REBUILD)
            new_after_rebuild = _get_count(cur.fetchone())

            # 4. проверка
            if missing_after_rebuild > 0 or new_after_rebuild > 0:
                LOGGER.error(
                    "snapshot inconsistency detected: missing=%s new=%s",
                    missing_after_rebuild,
                    new_after_rebuild,
                )
                raise RuntimeError(
                    "snapshot inconsistency detected: "
                    f"missing={missing_after_rebuild}, new={new_after_rebuild}"
                )

            LOGGER.info("snapshot consistent")