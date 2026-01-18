from datetime import datetime

from pydantic import BaseModel, Field

from .enums import ShipmentStatus


class Shipment(BaseModel):
    """
    Перевозка груза между складами.

    Возвращает только текущее состояние (без истории).
    """
    id: str = Field(..., description="Уникальный идентификатор перевозки")

    from_node: str = Field(
        ...,
        alias="from",
        description="Склад отправления (warehouse id)",
        examples=["spb-01"],
    )
    to_node: str = Field(
        ...,
        alias="to",
        description="Склад назначения (warehouse id)",
        examples=["msk-01"],
    )

    status: ShipmentStatus = Field(..., description="Текущий статус перевозки")

    updated_at: datetime = Field(
        ...,
        description="Дата и время последнего обновления состояния",
        examples=["2026-01-17T14:32:00Z"],
    )

    class Config:
        populate_by_name = True
