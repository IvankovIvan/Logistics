from __future__ import annotations

from collections.abc import Iterable, Mapping

from domain.coercion import coerce_enum, normalize_shipment, normalize_warehouse
from domain.protocols import ShipmentLike, WarehouseLike
from models import (
    MapResponse,
    MapRoute,
    MapWarehouse,
    ShipmentStatus,
    WarehouseStatus,
)


def build_map_response(
    warehouses_source: Iterable[WarehouseLike | Mapping[str, object]],
    shipments_source: Iterable[ShipmentLike | Mapping[str, object]],
) -> MapResponse:
    """
    Собирает данные карты из источников (FAKE_* или будущая БД/ингест).
    Здесь менять сборку, если модель данных или источники изменятся.
    """

    # 1) Склады: собираем geo-словарь id -> (lon, lat)
    warehouses: list[MapWarehouse] = []
    geo: dict[str, tuple[float, float]] = {}

    for raw in warehouses_source:
        w = normalize_warehouse(raw)
        if getattr(w, "lon", None) is None or getattr(w, "lat", None) is None:
            # Без координат точку на карту не ставим (иначе падает типизация/рендер).
            continue

        lon = float(w.lon)
        lat = float(w.lat)
        w_status = coerce_enum(
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

    # 2) Маршруты: shipments могут быть pydantic-моделями или dict
    routes: list[MapRoute] = []

    for raw in shipments_source:
        s = normalize_shipment(raw)
        from_id = str(s.from_node)
        to_id = str(s.to_node)

        from_geo = geo.get(from_id)
        to_geo = geo.get(to_id)
        if from_geo is None or to_geo is None:
            # Если складов нет в geo (нет координат/нет такого id) — линию не рисуем.
            continue

        status = coerce_enum(
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
