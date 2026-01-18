from typing import List

from pydantic import BaseModel, Field

from .map_warehouse import MapWarehouse
from .map_route import MapRoute


class MapResponse(BaseModel):
    """
    Ответ витрины карты.

    warehouses — склады с координатами
    routes — готовые линии маршрутов
    """
    warehouses: List[MapWarehouse] = Field(..., description="Склады для карты")
    routes: List[MapRoute] = Field(..., description="Маршруты для карты")