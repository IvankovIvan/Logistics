from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import cast

from fastapi import APIRouter

from domain.protocols import ShipmentLike, WarehouseLike
from models import MapResponse
from routers.shipments import FAKE_SHIPMENTS
from routers.warehouses import FAKE_WAREHOUSES
from services.map_builder import build_map_response

"""
HTTP-роутер /api/map

Назначение файла:
- принять HTTP-запрос
- передать данные в сервисный слой
- вернуть готовый MapResponse

Принципы:
- здесь НЕТ бизнес-логики
- здесь НЕТ преобразований данных
- здесь НЕТ работы с координатами и enum'ами

Почему:
- endpoint должен быть максимально тонким
- логику легко тестировать и переиспользовать
- FAKE_* можно заменить на БД/ингест без изменения API
"""


router = APIRouter(prefix="/api/map", tags=["map"])


@router.get(
    "",
    response_model=MapResponse,
    summary="Данные для карты",
    description=(
        "Единый endpoint для карты.\n\n"
        "Почему единый контракт:\n"
        "- Фронт делает 1 запрос и не склеивает данные.\n"
        "- Формат стабилен (можно заменить FAKE_* на БД без правок фронта).\n"
        "- Упрощает кеширование и версионирование.\n\n"
        "Что отдаём:\n"
        "- warehouses: точки (lon/lat)\n"
        "- routes: линии (from → to) + статус"
    ),
)
def get_map() -> MapResponse:
    """
    Endpoint карты.

    Здесь происходит ТОЛЬКО:
    - прокидывание источников данных в сервис
    - возврат готового MapResponse

    Почему используем cast(...):
    - FAKE_SHIPMENTS = list[Shipment] (pydantic-модель)
    - Shipment не считается подтипом ShipmentLike в Pylance:
        * Protocol
        * mutable поля
        * инвариантность типов
    - normalize_* в domain решает различия форматов
    """

    warehouses_src = cast(
        Iterable[WarehouseLike | Mapping[str, object]],
        FAKE_WAREHOUSES,
    )
    shipments_src = cast(
        Iterable[ShipmentLike | Mapping[str, object]],
        FAKE_SHIPMENTS,
    )

    return build_map_response(
        warehouses_source=warehouses_src,
        shipments_source=shipments_src,
    )