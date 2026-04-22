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

from fastapi import APIRouter, HTTPException, status

from app.services.analytics_map_builder import build_analytics_map_warehouses


LOGGER = logging.getLogger(__name__)

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
