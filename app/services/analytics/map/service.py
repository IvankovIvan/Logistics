"""Analytics map builder service for Project #3.

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

from dataclasses import dataclass

from app.repositories.map_repository import (
    fetch_warehouse_metrics,
    fetch_warehouses,
)
from app.services.analytics.utils import _as_mapping


@dataclass
class StatusQuantity:
    """Одна строка метрики по статусу склада."""

    status_id: int
    quantity: int


@dataclass
class WarehouseMetrics:
    """Агрегированные метрики склада."""

    total: int
    by_status: list[StatusQuantity]


@dataclass
class AnalyticsMapWarehouse:
    """Формат одного склада для Project #3 map API."""

    warehouse_id: int
    name: str
    lat: float
    lon: float
    metrics: WarehouseMetrics


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

    # 1) Справочник складов.
    warehouse_rows = fetch_warehouses()

    # 2) Агрегаты состояния по складам.
    metric_rows = fetch_warehouse_metrics()

    # Индекс метрик по складу для быстрого склеивания.
    metrics_by_warehouse: dict[int, WarehouseMetrics] = {}

    for raw_row in metric_rows:
        row = _as_mapping(raw_row)

        warehouse_id = int(row["warehouse_id"])
        status_id = int(row["status_id"])
        quantity = int(row["total_quantity"] or 0)
        warehouse_total_quantity = int(row["warehouse_total_quantity"] or 0)

        if warehouse_id not in metrics_by_warehouse:
            metrics_by_warehouse[warehouse_id] = WarehouseMetrics(
                total=warehouse_total_quantity,
                by_status=[],
            )

        metrics_by_warehouse[warehouse_id].by_status.append(
            StatusQuantity(
                status_id=status_id,
                quantity=quantity,
            )
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
            WarehouseMetrics(total=0, by_status=[]),
        )

        result.append(
            AnalyticsMapWarehouse(
                warehouse_id=int(warehouse_id),
                name=str(name),
                lat=float(lat),
                lon=float(lon),
                metrics=WarehouseMetrics(
                    total=int(metrics.total),
                    by_status=[
                        StatusQuantity(
                            status_id=int(status.status_id),
                            quantity=int(status.quantity),
                        )
                        for status in metrics.by_status
                    ],
                ),
            )
        )

    return result
