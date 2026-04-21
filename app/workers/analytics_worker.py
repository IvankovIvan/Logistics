# /opt/Logistics/app/workers/analytics_worker.py
"""
Micro-batch worker for Project #2 V2 analytics snapshot.

Инварианты:
- читает события строго по event_id
- НЕ пишет в inventory_status_events
- обновляет только current_batch_state и worker_state
- обрабатывает весь batch в одной транзакции
- watermark обновляется только после успешного batch commit
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Mapping
from typing import Any

from psycopg import Cursor

from app.services.analytics_ingest.connection import get_analytics_connection


LOGGER = logging.getLogger(__name__)

# ... imports остаются

# === КОНФИГ ===

# имя worker (используется в worker_state)
WORKER_NAME = "analytics_worker"

# размер batch (сколько событий за раз обрабатываем)
DEFAULT_BATCH_SIZE = 100

# задержка между итерациями
DEFAULT_SLEEP_SECONDS = 5

# === SQL: WATERMARK ===
# Берём текущую позицию worker
# FOR UPDATE блокирует строку → защита от двух worker
SELECT_WATERMARK = """
SELECT last_processed_event_id
FROM analytics.worker_state
WHERE worker_name = %(worker_name)s
FOR UPDATE;
"""

# === SQL: ЧТЕНИЕ СОБЫТИЙ ===
# Берём только новые события (event_id > watermark)
# ORDER BY гарантирует правильный порядок обработки
SELECT_EVENT_BATCH = """
SELECT
    e.event_id,
    e.batch_id,
    e.order_id,
    e.sku_id,
    e.warehouse_id,
    e.source_location_id,
    e.destination_location_id,
    e.status_id,
    e.status_reason_id,
    e.quantity,
    e.event_time,
    sr.is_tracking_finished
FROM analytics.inventory_status_events e
JOIN analytics.status_reason sr
    ON sr.status_reason_id = e.status_reason_id
WHERE e.event_id > %(last_processed_event_id)s
ORDER BY event_id
LIMIT %(batch_size)s;
"""

# === SQL: DELETE ===
# Удаляем партию ТОЛЬКО если событие новее текущего состояния
# Это защита от late events
DELETE_CURRENT_BATCH_STATE = """
DELETE FROM analytics.current_batch_state
WHERE batch_id = %(batch_id)s
    AND last_event_time < %(event_time)s;
"""

# === SQL: UPSERT ===
# Вставляем или обновляем состояние партии
# Обновляем ТОЛЬКО если событие новее
UPSERT_CURRENT_BATCH_STATE = """
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
VALUES (
    %(batch_id)s,
    %(order_id)s,
    %(sku_id)s,
    %(warehouse_id)s,
    %(status_id)s,
    %(quantity)s,
    %(source_location_id)s,
    %(destination_location_id)s,
    %(event_time)s
)
ON CONFLICT (batch_id) DO UPDATE
SET
    order_id = EXCLUDED.order_id,
    sku_id = EXCLUDED.sku_id,
    warehouse_id = EXCLUDED.warehouse_id,
    status_id = EXCLUDED.status_id,
    quantity = EXCLUDED.quantity,
    source_location_id = EXCLUDED.source_location_id,
    destination_location_id = EXCLUDED.destination_location_id,
    last_event_time = EXCLUDED.last_event_time
WHERE analytics.current_batch_state.last_event_time IS NULL
   OR EXCLUDED.last_event_time > analytics.current_batch_state.last_event_time;
"""

# === SQL: ОБНОВЛЕНИЕ WATERMARK ===
# GREATEST гарантирует, что watermark не откатится назад
UPDATE_WATERMARK = """
UPDATE analytics.worker_state
SET last_processed_event_id = GREATEST(
    last_processed_event_id,
    %(last_processed_event_id)s
)
WHERE worker_name = %(worker_name)s;
"""


def _get_batch_size() -> int:
    return int(os.getenv("ANALYTICS_WORKER_BATCH_SIZE", str(DEFAULT_BATCH_SIZE)))


def _get_sleep_seconds() -> int:
    return int(os.getenv("ANALYTICS_WORKER_SLEEP_SECONDS", str(DEFAULT_SLEEP_SECONDS)))


def _get_watermark(cur: Cursor[Any]) -> int:
    cur.execute(SELECT_WATERMARK, {"worker_name": WORKER_NAME})
    row = cur.fetchone()

    if row is None:
        raise RuntimeError(f"worker_state row not found for {WORKER_NAME}")

    if isinstance(row, Mapping):
        return int(row["last_processed_event_id"])
    return int(row[0])


def _load_batch(cur: Cursor[Any], last_processed_event_id: int, batch_size: int) -> list[Mapping[str, Any]]:
    cur.execute(
        SELECT_EVENT_BATCH,
        {
            "last_processed_event_id": last_processed_event_id,
            "batch_size": batch_size,
        },
    )
    rows = cur.fetchall()
    return list(rows)


def process_batch(batch_size: int | None = None) -> int:
    """
    Обрабатывает один analytics batch. 

    === ГАРАНТИИ ===
    - весь batch = одна транзакция 
    - если ошибка → rollback → batch перечитается на следующей итерации
    - система остаётся консистентной даже при late events и повторных запусках worker
    """

    effective_batch_size = batch_size or _get_batch_size()

    with get_analytics_connection() as conn:
        try:
            with conn.cursor() as cur:
                # 1. Берём текущий watermark (последний обработанный event_id)
                watermark = _get_watermark(cur)

                # 2. Загружаем события с event_id > watermark
                events = _load_batch(cur, watermark, effective_batch_size)
                
                # если событий нет → просто выходим (watermark не меняется)
                if not events:
                    conn.commit()
                    return 0

                last_processed_event_id = watermark

                # 3. Обрабатываем каждое событие по порядку
                for event in events:
                    event_id = int(event["event_id"])
                    batch_id = int(event["batch_id"])

                    # проверяем финальность партии по статусу причины
                    if bool(event["is_tracking_finished"]):
                        cur.execute(
                            # финальное событие → удаляем партию из current_batch_state (защита от late events)
                            DELETE_CURRENT_BATCH_STATE,
                            {
                                "batch_id": batch_id,
                                "event_time": event["event_time"],
                            },
                        )
                    else:
                        # обычное событие → обновляем snapshot в current_batch_state (UPSERT с проверкой по времени)
                        cur.execute(
                            UPSERT_CURRENT_BATCH_STATE,
                            {
                                "batch_id": batch_id,
                                "order_id": event["order_id"],
                                "sku_id": event["sku_id"],
                                "warehouse_id": event["warehouse_id"],
                                "status_id": event["status_id"],
                                "quantity": event["quantity"],
                                "source_location_id": event["source_location_id"],
                                "destination_location_id": event[
                                    "destination_location_id"
                                ],
                                "event_time": event["event_time"],
                            },
                        )

                    # обновляем локальный watermark только после успешной обработки события 
                    last_processed_event_id = event_id

                # 4. Обновляем watermark в БД только после успешного commit всей партии
                cur.execute(
                    UPDATE_WATERMARK,
                    {
                        "worker_name": WORKER_NAME,
                        "last_processed_event_id": last_processed_event_id,
                    },
                )

            # 5. commit всей транзакции (включая обновление snapshot и watermark)
            conn.commit()
            return len(events)
        except Exception:
            # при любой ошибке → откат всей транзакции → batch будет перечитан на следующей итерации
            conn.rollback()
            raise


def run_worker() -> None:
    """
    Бесконечный цикл micro-batch worker.

    Каждая итерация:
    - читает watermark
    - читает новый batch событий
    - обновляет snapshot
    - обновляет watermark
    - засыпает на заданный интервал
    """

    sleep_seconds = _get_sleep_seconds()

    LOGGER.info(
        "Starting analytics worker with batch_size=%s sleep_seconds=%s",
        _get_batch_size(),
        sleep_seconds,
    )

    while True:
        processed = process_batch()

        if processed > 0:
            LOGGER.info("Processed analytics batch: %s events", processed)

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker()