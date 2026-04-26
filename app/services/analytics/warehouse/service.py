"""Warehouse analytics service for metadata, metrics, and batch data."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from app.repositories.warehouse_repository import (
    fetch_warehouse_batches,
    fetch_warehouse_metadata,
    fetch_warehouse_metrics,
)
from app.services.analytics.utils import _as_mapping


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
    last_event_time: datetime | None


def get_analytics_warehouse_metadata(
    warehouse_id: int,
) -> WarehouseRow | None:
    """
    Возвращает metadata одного склада из analytics-справочников.

    Если склад не найден, возвращает None.
    """

    raw_row = fetch_warehouse_metadata(warehouse_id)

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

    raw_rows = fetch_warehouse_metrics(warehouse_id)

    rows = [_as_mapping(raw_row) for raw_row in raw_rows]

    result: list[WarehouseMetricRow] = []

    for row in rows:
        status_text = row["status_text"] or ""

        result.append(
            {
                "status_id": int(row["status_id"]),
                "status_text": str(status_text),
                "count": int(row["count"]),
                "sum": int(row["sum"]),
                "total_count": int(row["total_count"]),
                "total_sum": int(row["total_sum"]),
            }
        )

    return result


def get_analytics_warehouse_batches(warehouse_id: int) -> list[WarehouseBatchRow]:
    """Возвращает список партий склада для CSV выгрузки."""

    raw_rows = fetch_warehouse_batches(warehouse_id)

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
