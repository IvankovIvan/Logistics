from pydantic import BaseModel, Field

from typing import Optional

from .enums import WarehouseStatus


class Warehouse(BaseModel):
    """
    Склад / логистический узел.

    Используется как точка отправки или назначения перевозок.
    """
    id: str = Field(..., description="Уникальный идентификатор склада")
    name: str = Field(..., description="Человекочитаемое название склада")
    status: WarehouseStatus = Field(..., description="Текущий статус склада")

    # Координаты для карты (MapLibre). Optional, чтобы можно было жить без гео.
    lat: Optional[float] = Field(None, description="Широта склада", examples=[59.9311])
    lon: Optional[float] = Field(None, description="Долгота склада", examples=[30.3609])
