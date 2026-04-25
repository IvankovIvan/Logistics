"""
Экспорт всех Pydantic-моделей приложения.

Используется для:
- единых импортов в роутерах
- читаемости
- явного API моделей
"""

# базовые enum’ы
from .enums import WarehouseStatus, ShipmentStatus

# основные доменные модели
from .warehouse import Warehouse
from .shipment import Shipment

# витрины / проекции
from .map_warehouse import MapWarehouse
from .map_route import MapRoute
from .map_response import MapResponse

__all__ = [
    # enums
    "WarehouseStatus",
    "ShipmentStatus",

    # core models
    "Warehouse",
    "Shipment",

    # map projection
    "MapWarehouse",
    "MapRoute",
    "MapResponse",
]