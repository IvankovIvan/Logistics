from __future__ import annotations

from typing import Any, Dict, List, Tuple, Type, TypeVar, cast

from fastapi import APIRouter

from models import (
    MapResponse,
    MapRoute,
    MapWarehouse,
    ShipmentStatus,
    WarehouseStatus,
)
from routers.shipments import FAKE_SHIPMENTS
from routers.warehouses import FAKE_WAREHOUSES

router = APIRouter(prefix="/map", tags=["map"])

TEnum = TypeVar("TEnum")


def _get(obj: Any, key: str) -> Any:
    """
    Универсально достаёт поле и из dict, и из pydantic-модели.

    Зачем:
    - Сейчас у нас FAKE_WAREHOUSES = list[dict]
    - А FAKE_SHIPMENTS = list[Shipment] (pydantic BaseModel)
    - Чтобы /map работал и при будущей замене источника данных.
    """
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _as_enum(value: Any, enum_cls: Type[TEnum], default: TEnum) -> TEnum:
    """
    Приводит value к enum, но безопасно.

    Важно:
    - value может быть уже enum'ом (ShipmentStatus.in_transit)
    - может быть строкой ('in_transit')
    - может быть None/мусором
    """
    if isinstance(value, enum_cls):
        return value
    if value is None:
        return default
    try:
        return enum_cls(str(value))  # type: ignore[misc]
    except Exception:
        return default


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
    # 1) Склады: собираем geo-словарь id -> (lon, lat)
    warehouses: List[MapWarehouse] = []
    geo: Dict[str, Tuple[float, float]] = {}

    for w in cast(List[Any], FAKE_WAREHOUSES):
        wid = cast(str, _get(w, "id"))
        name = cast(str, _get(w, "name"))

        lon_raw = _get(w, "lon")
        lat_raw = _get(w, "lat")
        if lon_raw is None or lat_raw is None:
            # Без координат точку на карту не ставим (иначе падает типизация/рендер).
            continue

        lon = float(lon_raw)
        lat = float(lat_raw)

        w_status_raw = _get(w, "status")
        w_status = _as_enum(w_status_raw, WarehouseStatus, WarehouseStatus.active)

        warehouses.append(
            MapWarehouse(
                id=wid,
                name=name,
                status=w_status,
                lon=lon,
                lat=lat,
            )
        )
        geo[wid] = (lon, lat)

    # 2) Маршруты: FAKE_SHIPMENTS у тебя = list[Shipment], поэтому читаем атрибуты
    routes: List[MapRoute] = []

    for s in cast(List[Any], FAKE_SHIPMENTS):
        sid = cast(str, _get(s, "id"))
        from_id = cast(str, _get(s, "from_node"))
        to_id = cast(str, _get(s, "to_node"))

        from_geo = geo.get(from_id)
        to_geo = geo.get(to_id)
        if from_geo is None or to_geo is None:
            # Если складов нет в geo (нет координат/нет такого id) — линию не рисуем.
            continue

        status_raw = _get(s, "status")
        status = _as_enum(status_raw, ShipmentStatus, ShipmentStatus.planned)

        from_lon, from_lat = from_geo
        to_lon, to_lat = to_geo

        routes.append(
            MapRoute(
                id=sid,
                status=status,
                **{"from": from_id, "to": to_id},  # from/to — ключевые слова в python
                coordinates=[
                    (from_lon, from_lat),
                    (to_lon, to_lat),
                ],
            )
        )

    return MapResponse(warehouses=warehouses, routes=routes)