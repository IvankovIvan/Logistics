from datetime import datetime
from typing import List, Literal, Union
from typing_extensions import Annotated
from pydantic import BaseModel, Field


# =====================================================
# Payloads (entity-specific)
# =====================================================

class WarehouseUpsertPayload(BaseModel):
    """
    Полный current-state склада.
    Частичные апдейты запрещены.
    """
    id: str = Field(..., description="Уникальный идентификатор склада")
    name: str = Field(..., description="Отображаемое имя склада")
    lat: float = Field(..., description="Широта")
    lon: float = Field(..., description="Долгота")
    status: str = Field(..., description="Текущий статус склада")
    quantity: int = Field(..., description="Текущее количество товара на складе")


class ShipmentUpsertPayload(BaseModel):
    """
    Полный current-state перевозки (маршрута).
    """
    id: str = Field(..., description="Уникальный идентификатор перевозки")
    from_warehouse_id: str = Field(..., description="Склад-источник")
    to_warehouse_id: str = Field(..., description="Склад-назначения")
    status: str = Field(..., description="Текущий статус перевозки")


# =====================================================
# Discriminated ingest events
# =====================================================

class WarehouseIngestEvent(BaseModel):
    """
    Ingest-событие для склада.
    """
    event_id: str = Field(
        ...,
        description="Глобально уникальный идентификатор события (идемпотентность)"
    )
    event_time: datetime = Field(
        ...,
        description="Время факта (секунды). Защита от устаревших данных."
    )
    entity_type: Literal["warehouse"] = Field(
        "warehouse",
        description="Тип сущности"
    )
    payload: WarehouseUpsertPayload


class ShipmentIngestEvent(BaseModel):
    """
    Ingest-событие для перевозки.
    """
    event_id: str = Field(
        ...,
        description="Глобально уникальный идентификатор события (идемпотентность)"
    )
    event_time: datetime = Field(
        ...,
        description="Время факта (секунды). Защита от устаревших данных."
    )
    entity_type: Literal["shipment"] = Field(
        "shipment",
        description="Тип сущности"
    )
    payload: ShipmentUpsertPayload


# =====================================================
# Union с discriminator
# =====================================================

IngestEvent = Annotated[
    Union[WarehouseIngestEvent, ShipmentIngestEvent],
    Field(discriminator="entity_type"),
]


class IngestBatch(BaseModel):
    """
    Batch ingest-событий.

    - события независимы
    - частичный успех — норма
    """
    events: List[IngestEvent] = Field(
        ...,
        description="Список ingest-событий"
    )
