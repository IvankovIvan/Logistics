# app/services/ingest/map_builder.py
from __future__ import annotations

from collections.abc import Iterable, Mapping

from app.domain.coercion import coerce_enum, normalize_shipment, normalize_warehouse
from app.domain.protocols import ShipmentLike, WarehouseLike
from models import (
    MapResponse,
    MapRoute,
    MapWarehouse,
    ShipmentStatus,
    WarehouseStatus,
)

from app.services.data_sources.base import CurrentStateDataSource
from app.services.data_sources.selector import get_current_state_data_source


# ============================================================================
# Источник current-state данных для карты
# ----------------------------------------------------------------------------
# ВАЖНО:
# - map_builder НЕ знает, откуда берутся данные (FAKE / БД / кэш)
# - он работает только с read-интерфейсом CurrentStateDataSource
# - замена источника НЕ должна менять логику ниже
# ============================================================================
# _data_source: CurrentStateDataSource = get_current_state_data_source()


def build_map_response(
    warehouses_source: Iterable[WarehouseLike | Mapping[str, object]] | None = None,
    shipments_source: Iterable[ShipmentLike | Mapping[str, object]] | None = None,
) -> MapResponse:
    """
    Собирает витрину карты (/api/map) из current-state данных.

    Назначение функции:
    - превратить *текущее состояние логистики* в MapResponse
    - нормализовать входные данные (dict / pydantic / domain-модели)
    - вычислить derived-данные (статусы, координаты маршрутов)

    ВАЖНЫЕ ИНВАРИАНТЫ:
    - функция НЕ знает про ingest, события и БД
    - функция НЕ хранит состояние
    - функция НЕ меняет данные, только интерпретирует их
    - контракт MapResponse стабилен

    Источники данных:
    - по умолчанию используются данные из CurrentStateDataSource
    - аргументы warehouses_source / shipments_source оставлены
      для тестов и явной подстановки источников
    """

    # ------------------------------------------------------------------------
    # 0) Выбор current-state источника (на каждый вызов)
    # ------------------------------------------------------------------------
    data_source: CurrentStateDataSource = get_current_state_data_source()

    # ------------------------------------------------------------------------
    # 1) Получение current-state данных
    # ------------------------------------------------------------------------
    # Если источники не переданы явно — читаем snapshot из data source.
    if warehouses_source is None:
        warehouses_source = data_source.get_warehouses()

    if shipments_source is None:
        shipments_source = data_source.get_shipments()

    # ------------------------------------------------------------------------
    # 2) Склады: собираем geo-словарь id -> (lon, lat)
    # ------------------------------------------------------------------------
    warehouses: list[MapWarehouse] = []
    geo: dict[str, tuple[float, float]] = {}

    for raw in warehouses_source:
        w = normalize_warehouse(raw)

        if getattr(w, "lon", None) is None or getattr(w, "lat", None) is None:
            # Без координат точку на карту не ставим:
            # - фронт не умеет рендерить "пустые" точки
            # - карта должна быть устойчивой к частичным данным
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

    # ------------------------------------------------------------------------
    # 3) Маршруты: shipments могут быть dict или доменными моделями
    # ------------------------------------------------------------------------
    routes: list[MapRoute] = []

    for raw in shipments_source:
        s = normalize_shipment(raw)

        from_id = str(s.from_node)
        to_id = str(s.to_node)

        from_geo = geo.get(from_id)
        to_geo = geo.get(to_id)

        if from_geo is None or to_geo is None:
            # Если хотя бы одной точки нет — маршрут не рисуем
            # (нет координат или склад отсутствует в current-state)
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
                **{"from": from_id, "to": to_id},  # from/to — ключевые слова Python
                coordinates=[
                    (from_lon, from_lat),
                    (to_lon, to_lat),
                ],
            )
        )

    # ------------------------------------------------------------------------
    # 4) Финальная витрина карты
    # ------------------------------------------------------------------------
    return MapResponse(
        warehouses=warehouses,
        routes=routes,
    )