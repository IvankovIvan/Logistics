# app/routers/analytics_map.py

"""
HTTP-роутер для карты Project #3 (analytics layer).

Назначение:
- отдать данные карты из analytics-слоя
- не использовать старый map_builder
- не трогать существующий /api/map
"""

from __future__ import annotations

import logging
from typing import TypedDict, cast

from fastapi import APIRouter, HTTPException, status
from app.models.analytics.warehouse_metadata import AnalyticsWarehouseMetadata

from app.services.analytics_map_builder import (
    build_analytics_map_warehouses,
    get_analytics_warehouse_metadata,
)


LOGGER = logging.getLogger(__name__)


class _WarehouseRow(TypedDict):
    warehouse_id: int
    name: str
    city: str
    warehouse_type: str

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics-map"],
)


@router.get(
    "/map",
    status_code=status.HTTP_200_OK,
    summary="Analytics map data (Project #3)",
    description=(
        "Возвращает данные карты из analytics-слоя.\n\n"
        "- warehouses: агрегированные метрики по складам\n"
        "- routes: пока пустой массив (V1)"
    ),
)
def get_analytics_map() -> dict[str, object]:
    """
    Endpoint Project #3 карты.

    ВАЖНО:
    - источник данных: analytics_map_builder
    - OLTP и старый map_builder не используются
    - формат ответа плоский и совместим с будущим map API
    """

    try:
        data = build_analytics_map_warehouses()
        return {
            "warehouses": data,
            "routes": [],
        }
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

    return AnalyticsWarehouseMetadata(
        warehouse_id=row_typed["warehouse_id"],
        name=row_typed["name"],
        city=row_typed["city"],
        warehouse_type=row_typed["warehouse_type"],
    )
