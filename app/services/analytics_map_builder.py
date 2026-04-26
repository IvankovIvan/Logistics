"""
Analytics map builder for Project #3.

Назначение:
- собрать карту из analytics-слоя (без OLTP)
- использовать master-справочник складов analytics.warehouses
- использовать агрегаты из analytics.current_batch_state
- вернуть структуру, удобную для API-слоя карты

Инварианты:
- НЕ трогает существующий app/services/map_builder.py
- НЕ использует JSON в SQL
- НЕ использует status_reason_id
- НЕ фильтрует склады: каждый warehouse из справочника попадает в ответ
"""

from __future__ import annotations

from typing import TypedDict

from app.services.analytics.utils import _as_mapping
from app.services.analytics_ingest.connection import get_analytics_connection


class StatusQuantity(TypedDict):
    """Одна строка метрики по статусу склада."""

    status_id: int
    quantity: int


class WarehouseMetrics(TypedDict):
    """Агрегированные метрики склада."""

    total: int
    by_status: list[StatusQuantity]


class AnalyticsMapWarehouse(TypedDict):
    """Формат одного склада для Project #3 map API."""

    warehouse_id: int
    name: str
    lat: float
    lon: float
    metrics: WarehouseMetrics


SELECT_WAREHOUSES = """
SELECT
    warehouse_id,
    name,
    lat,
    lon
FROM analytics.warehouses
ORDER BY warehouse_id;
"""


SELECT_AGGREGATED_METRICS = """
WITH aggregated AS (
    -- Агрегация количества по складу и статусу.
    SELECT
        warehouse_id,
        status_id,
        SUM(quantity) AS total_quantity
    FROM analytics.current_batch_state
    GROUP BY
        warehouse_id,
        status_id
)
SELECT
    warehouse_id,
    status_id,
    total_quantity,
    -- Общий объём по складу (без разреза по статусам).
    SUM(total_quantity) OVER (
        PARTITION BY warehouse_id
    ) AS warehouse_total_quantity
FROM aggregated
ORDER BY
    warehouse_id,
    status_id;
"""


def build_analytics_map_warehouses() -> list[AnalyticsMapWarehouse]:
    """
    Собирает map-структуру складов из analytics.

    Алгоритм:
    1) Читаем master-справочник складов (analytics.warehouses).
    2) Читаем агрегаты по складам/статусам (analytics.current_batch_state).
    3) Склеиваем в Python по warehouse_id (LEFT JOIN-логика):
       - склад есть всегда, даже если для него нет строк в агрегате
       - при отсутствии агрегатов: total=0, by_status=[]

    Возвращает плоский список объектов:
    {
      warehouse_id,
      lat,
      lon,
      metrics: {
        total,
        by_status: [{status_id, quantity}, ...]
      }
    }
    """

    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            # 1) Справочник складов.
            cur.execute(SELECT_WAREHOUSES)
            warehouse_rows = cur.fetchall()

            # 2) Агрегаты состояния по складам.
            cur.execute(SELECT_AGGREGATED_METRICS)
            metric_rows = cur.fetchall()

    # Индекс метрик по складу для быстрого склеивания.
    metrics_by_warehouse: dict[int, WarehouseMetrics] = {}

    for raw_row in metric_rows:
        row = _as_mapping(raw_row)

        warehouse_id = int(row["warehouse_id"])
        status_id = int(row["status_id"])
        quantity = int(row["total_quantity"] or 0)
        warehouse_total_quantity = int(row["warehouse_total_quantity"] or 0)

        if warehouse_id not in metrics_by_warehouse:
            metrics_by_warehouse[warehouse_id] = {
                "total": warehouse_total_quantity,
                "by_status": [],
            }

        metrics_by_warehouse[warehouse_id]["by_status"].append(
            {
                "status_id": status_id,
                "quantity": quantity,
            }
        )

    # Финальная сборка: НЕ теряем склады без метрик.
    result: list[AnalyticsMapWarehouse] = []

    for raw_row in warehouse_rows:
        row = _as_mapping(raw_row)

        warehouse_id = int(row["warehouse_id"])
        name = str(row["name"])
        lat = float(row["lat"])
        lon = float(row["lon"])

        metrics = metrics_by_warehouse.get(
            warehouse_id,
            {
                "total": 0,
                "by_status": [],
            },
        )

        result.append(
            {
                "warehouse_id": warehouse_id,
                "name": name,
                "lat": lat,
                "lon": lon,
                "metrics": metrics,
            }
        )

    return result
