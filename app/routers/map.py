from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from types import SimpleNamespace
from typing import Protocol, Type, TypeVar

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

router = APIRouter(prefix="/api/map", tags=["map"])


class WarehouseLike(Protocol):
    id: str
    name: str
    lon: float | int | str
    lat: float | int | str
    status: WarehouseStatus | str | None


class ShipmentLike(Protocol):
    id: str
    from_node: str
    to_node: str
    status: ShipmentStatus | str | None


TEnum = TypeVar("TEnum", bound=Enum)


def _as_warehouse(item: WarehouseLike | Mapping[str, object]) -> WarehouseLike:
    if isinstance(item, Mapping):
        # Normalize dicts so all access is attribute-based.
        return SimpleNamespace(**item)  # type: ignore[return-value]
    return item


def _as_shipment(item: ShipmentLike | Mapping[str, object]) -> ShipmentLike:
    if isinstance(item, Mapping):
        # Normalize dicts so all access is attribute-based.
        return SimpleNamespace(**item)  # type: ignore[return-value]
    return item


def _coerce_enum(value: object, enum_cls: Type[TEnum], default: TEnum) -> TEnum:
    if isinstance(value, enum_cls):
        return value
    if value is None:
        return default
    try:
        return enum_cls(str(value))
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
    warehouses: list[MapWarehouse] = []
    geo: dict[str, tuple[float, float]] = {}

    for raw in FAKE_WAREHOUSES:
        w = _as_warehouse(raw)
        if getattr(w, "lon", None) is None or getattr(w, "lat", None) is None:
            # Без координат точку на карту не ставим (иначе падает типизация/рендер).
            continue

        lon = float(w.lon)
        lat = float(w.lat)
        w_status = _coerce_enum(
            getattr(w, "status", None),
            WarehouseStatus,
            WarehouseStatus.active,
        )

        wid = str(w.id)
        name = str(w.name)
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
    routes: list[MapRoute] = []

    for raw in FAKE_SHIPMENTS:
        s = _as_shipment(raw)
        from_id = str(s.from_node)
        to_id = str(s.to_node)

        from_geo = geo.get(from_id)
        to_geo = geo.get(to_id)
        if from_geo is None or to_geo is None:
            # Если складов нет в geo (нет координат/нет такого id) — линию не рисуем.
            continue

        status = _coerce_enum(
            getattr(s, "status", None),
            ShipmentStatus,
            ShipmentStatus.planned,
        )

        from_lon, from_lat = from_geo
        to_lon, to_lat = to_geo

        routes.append(
            MapRoute(
                id=str(s.id),
                status=status,
                **{"from": from_id, "to": to_id},  # from/to — ключевые слова в python
                coordinates=[
                    (from_lon, from_lat),
                    (to_lon, to_lat),
                ],
            )
        )

    return MapResponse(warehouses=warehouses, routes=routes)
