"""Warehouse analytics service for metadata, metrics, and batch data."""

from __future__ import annotations

from typing import TypedDict

from app.services.analytics.utils import _as_mapping
from app.services.db.connection import get_analytics_connection


SELECT_WAREHOUSE_METADATA = """
SELECT
    w.warehouse_id,
    w.name,
    c.name AS city,
    wt.name AS warehouse_type
FROM analytics.warehouses w
JOIN analytics.cities c
    ON c.city_id = w.city_id
JOIN analytics.warehouse_types wt
    ON wt.warehouse_type_id = w.warehouse_type_id
WHERE w.warehouse_id = %(warehouse_id)s;
"""


SELECT_WAREHOUSE_METRICS = """
WITH base AS (
    SELECT
        status_id,
        quantity
    FROM analytics.current_batch_state
    WHERE warehouse_id = %(warehouse_id)s
),

totals AS (
    SELECT
        COUNT(*) AS total_count,
        SUM(quantity) AS total_sum
    FROM base
),

by_status AS (
    SELECT
        b.status_id,
        COUNT(*) AS count,
        SUM(b.quantity) AS sum
    FROM base b
    GROUP BY b.status_id
)

SELECT
    bs.status_id,
    d.description AS status_text,
    bs.count,
    bs.sum,
    t.total_count,
    t.total_sum
FROM by_status bs
LEFT JOIN analytics.status_dict d
    ON d.status_id = bs.status_id
CROSS JOIN totals t
ORDER BY bs.sum DESC;
"""


SELECT_WAREHOUSE_BATCHES = """
SELECT
    batch_id,
    status_id,
    quantity,
    warehouse_id,
    last_event_time
FROM analytics.current_batch_state
WHERE warehouse_id = %(warehouse_id)s
ORDER BY last_event_time DESC;
"""


class WarehouseRow(TypedDict):
    warehouse_id: int
    name: str
    city: str
    warehouse_type: str


class WarehouseMetricRow(TypedDict):
    status_id: int
    status_text: str
    count: int
    sum: int
    total_count: int
    total_sum: int


class WarehouseBatchRow(TypedDict):
    batch_id: int
    status_id: int
    quantity: int
    warehouse_id: int
    last_event_time: object


def get_analytics_warehouse_metadata(
    warehouse_id: int,
) -> WarehouseRow | None:
    """
    Возвращает metadata одного склада из analytics-справочников.

    Если склад не найден, возвращает None.
    """

    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                SELECT_WAREHOUSE_METADATA,
                {"warehouse_id": warehouse_id},
            )
            raw_row = cur.fetchone()

    if raw_row is None:
        return None

    row = _as_mapping(raw_row)

    return {
        "warehouse_id": int(row["warehouse_id"]),
        "name": str(row["name"]),
        "city": str(row["city"]),
        "warehouse_type": str(row["warehouse_type"]),
    }


def get_analytics_warehouse_metrics(warehouse_id: int) -> list[WarehouseMetricRow]:
    """
    Возвращает агрегированные метрики склада из current_batch_state.

    Один SQL-запрос:
    - by_status (count/sum)
    - total_count/total_sum через window functions.
    """

    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                SELECT_WAREHOUSE_METRICS,
                {"warehouse_id": warehouse_id},
            )
            raw_rows = cur.fetchall()

    rows = [_as_mapping(raw_row) for raw_row in raw_rows]

    return [
        {
            "status_id": int(row["status_id"]),
            "status_text": str(row["status_text"]),
            "count": int(row["count"]),
            "sum": int(row["sum"]),
            "total_count": int(row["total_count"]),
            "total_sum": int(row["total_sum"]),
        }
        for row in rows
    ]


def get_analytics_warehouse_batches(warehouse_id: int) -> list[WarehouseBatchRow]:
    """Возвращает список партий склада для CSV выгрузки."""

    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                SELECT_WAREHOUSE_BATCHES,
                {"warehouse_id": warehouse_id},
            )
            raw_rows = cur.fetchall()

    rows = [_as_mapping(raw_row) for raw_row in raw_rows]

    return [
        {
            "batch_id": int(row["batch_id"]),
            "status_id": int(row["status_id"]),
            "quantity": int(row["quantity"]),
            "warehouse_id": int(row["warehouse_id"]),
            "last_event_time": row["last_event_time"],
        }
        for row in rows
    ]
