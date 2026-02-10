from pydantic import BaseModel, Field

from .enums import WarehouseStatus


class MapWarehouse(BaseModel):
    """
    Склад для карты (с координатами).

    Это витринная модель: фронту не нужно угадывать координаты по id.
    """
    id: str = Field(..., description="ID склада")
    name: str = Field(..., description="Название склада")
    status: WarehouseStatus = Field(..., description="Статус склада")

    lon: float = Field(..., description="Долгота (WGS84)", examples=[30.3141])
    lat: float = Field(..., description="Широта (WGS84)", examples=[59.9386])
    quantity: int = Field(..., description="Текущее количество товара на складе")
