from __future__ import annotations

from fastapi import APIRouter

from models import (
    MapResponse,
)
from routers.shipments import FAKE_SHIPMENTS
from routers.warehouses import FAKE_WAREHOUSES
from services.map_builder import build_map_response

router = APIRouter(prefix="/api/map", tags=["map"])


@router.get(
    "",
    response_model=MapResponse,
    summary="Данные для карты",
    description=(
        "Единый endpoint для карты.\n\n"
        "Почему так:\n"
        "- Фронт делает 1 запрос и не склеивает данные.\n"
        "- Формат стабилен: можно заменить FAKE_* на БД/ингест без правок фронта.\n\n"
        "Что отдаём:\n"
        "- warehouses: точки (lon/lat)\n"
        "- routes: линии (2 координаты: from->to) + статус"
    ),
)
def get_map() -> MapResponse:
    # Здесь только endpoint: источник данных (FAKE_*) заменим на БД/ингест в сервисе.
    return build_map_response(FAKE_WAREHOUSES, FAKE_SHIPMENTS)
