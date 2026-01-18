from pydantic import BaseModel, Field

from .enums import WarehouseStatus


class Warehouse(BaseModel):
    """
    Склад / логистический узел.

    Используется как точка отправки или назначения перевозок.
    """
    id: str = Field(..., description="Уникальный идентификатор склада")
    name: str = Field(..., description="Человекочитаемое название склада")
    status: WarehouseStatus = Field(..., description="Текущий статус склада")
