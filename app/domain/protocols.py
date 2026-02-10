from __future__ import annotations

from typing import Protocol

from app.models.shipment import ShipmentStatus
from app.models.warehouse import WarehouseStatus


class WarehouseLike(Protocol):
    """
    Минимальный контракт склада для карты.

    Зачем:
    - /api/map должен уметь работать и с FAKE_* (dict), и с будущей БД/ингестом (объекты).
    - Поэтому дальше мы нормализуем входные данные к объекту с атрибутами.

    Когда менять:
    - Если переедем на новую модель склада (поля/названия/типы) — правим здесь.
    """

    id: str
    name: str
    lon: float | int | str
    lat: float | int | str
    status: WarehouseStatus | str | None
    quantity: int | str


class ShipmentLike(Protocol):
    """
    Минимальный контракт перевозки/отправки для карты.

    Примечание:
    - В модели Shipment у нас поля называются from_node/to_node (не from/to),
      потому что from/to — ключевые слова в Python.

    Когда менять:
    - Если переедем на новую модель shipment или поменяем названия полей — правим здесь.
    """

    id: str
    from_node: str
    to_node: str
    status: ShipmentStatus | str | None
