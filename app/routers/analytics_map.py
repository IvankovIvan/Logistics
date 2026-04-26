# app/routers/analytics_map.py

"""
HTTP-роутер для карты Project #3 (analytics layer).

Назначение:
- отдать данные карты из analytics-слоя
- не использовать старый map_builder
- не трогать существующий /api/map
"""

from __future__ import annotations

import csv
import io
import logging
from typing import TypedDict, cast

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.analytics.warehouse_metadata import (
    AnalyticsWarehouseMetadata,
    AnalyticsWarehouseMetrics,
    AnalyticsWarehouseStatus,
)
from app.models.analytics_map_response import (
    AnalyticsMapResponse,
    MapWarehouse,
    WarehouseMetrics,
    StatusQuantity,
)

from app.services.analytics.warehouse.service import (
    get_analytics_warehouse_batches,
    get_analytics_warehouse_metrics,
    get_analytics_warehouse_metadata,
)
from app.services.analytics.map.service import (
    build_analytics_map_warehouses,
)


LOGGER = logging.getLogger(__name__)


class _WarehouseRow(TypedDict):
    warehouse_id: int
    name: str
    city: str
    warehouse_type: str


class _WarehouseMetricRow(TypedDict):
    status_id: int
    status_text: str
    count: int
    sum: int
    total_count: int
    total_sum: int


class _WarehouseBatchRow(TypedDict):
    batch_id: int
    status_id: int
    quantity: int
    warehouse_id: int
    last_event_time: object

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics-map"],
)


@router.get(
    "/map",
    response_model=AnalyticsMapResponse,
    status_code=status.HTTP_200_OK,
    summary="Analytics map data (Project #3)",
    description=(
        "Возвращает данные карты из analytics-слоя.\n\n"
        "- warehouses: агрегированные метрики по складам\n"
        "- routes: пока пустой массив (V1)"
    ),
)
def get_analytics_map() -> AnalyticsMapResponse:
    """
    Endpoint Project #3 карты.

    ВАЖНО:
    - источник данных: analytics_map_builder
    - OLTP и старый map_builder не используются
    - формат ответа плоский и совместим с будущим map API
    """

    try:
        raw_data = build_analytics_map_warehouses()

        warehouses = []

        for item in raw_data:
            metrics = item["metrics"]

            warehouses.append(
                MapWarehouse(
                    warehouse_id=item["warehouse_id"],
                    name=item["name"],
                    lat=item["lat"],
                    lon=item["lon"],
                    metrics=WarehouseMetrics(
                        total=metrics["total"],
                        by_status=[
                            StatusQuantity(
                                status_id=s["status_id"],
                                quantity=s["quantity"],
                            )
                            for s in metrics["by_status"]
                        ],
                    ),
                )
            )

        return AnalyticsMapResponse(
            warehouses=warehouses,
            routes=[],
        )
    except Exception as exc:
        LOGGER.exception("Failed to build analytics map response")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build analytics map",
        ) from exc


@router.get(
    "/warehouse/{warehouse_id}",
    status_code=status.HTTP_200_OK,
    response_model=AnalyticsWarehouseMetadata,
    summary="Analytics warehouse metadata",
    description=(
        "Возвращает metadata склада из analytics-слоя: "
        "warehouse_id, name, city, warehouse_type."
    ),
)
def get_analytics_warehouse(warehouse_id: int) -> AnalyticsWarehouseMetadata:
    """Metadata одного склада из analytics справочников."""

    row = get_analytics_warehouse_metadata(warehouse_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found",
        )

    row_typed = cast(_WarehouseRow, row)

    metric_rows = get_analytics_warehouse_metrics(warehouse_id)

    if metric_rows:
        first_metric_row = cast(_WarehouseMetricRow, metric_rows[0])
        total_count = int(first_metric_row["total_count"])
        total_sum = int(first_metric_row["total_sum"])
    else:
        total_count = 0
        total_sum = 0

    by_status: list[AnalyticsWarehouseStatus] = []
    for metric_row in metric_rows:
        metric_row_typed = cast(_WarehouseMetricRow, metric_row)
        by_status.append(
            AnalyticsWarehouseStatus(
                status_id=int(metric_row_typed["status_id"]),
                status_text=str(metric_row_typed["status_text"]),
                count=int(metric_row_typed["count"]),
                sum=int(metric_row_typed["sum"]),
            )
        )

    metrics_model = AnalyticsWarehouseMetrics(
        count=total_count,
        sum=total_sum,
        by_status=by_status,
    )

    return AnalyticsWarehouseMetadata(
        warehouse_id=row_typed["warehouse_id"],
        name=row_typed["name"],
        city=row_typed["city"],
        warehouse_type=row_typed["warehouse_type"],
        metrics=metrics_model,
    )


@router.get(
    "/warehouse/{warehouse_id}/batches.csv",
    status_code=status.HTTP_200_OK,
    summary="Export warehouse batches CSV",
    description="Скачивание CSV со списком партий склада",
)
def export_analytics_warehouse_batches_csv(warehouse_id: int) -> StreamingResponse:
    rows = get_analytics_warehouse_batches(warehouse_id)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "batch_id",
        "status_id",
        "quantity",
        "warehouse_id",
        "last_event_time",
    ])

    for row in rows:
        row_typed = cast(_WarehouseBatchRow, row)
        writer.writerow(
            [
                row_typed["batch_id"],
                row_typed["status_id"],
                row_typed["quantity"],
                row_typed["warehouse_id"],
                row_typed["last_event_time"],
            ]
        )

    headers = {
        "Content-Disposition": (
            f'attachment; filename="warehouse_{warehouse_id}_batches.csv"'
        )
    }

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers=headers,
    )
