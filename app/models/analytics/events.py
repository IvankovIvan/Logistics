# app/models/analytics/events.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyticsEvent(BaseModel):
    """
    Одно событие для analytics event store.

    operation_id используется как бизнес-ключ идемпотентности
    (совместно с event_time).
    """

    operation_id: int = Field(
        ...,
        description="Бизнес-ключ операции (идемпотентность вместе с event_time)",
    )
    batch_id: int = Field(..., description="ID партии (batch)")
    order_id: int = Field(..., description="ID заказа")
    sku_id: int = Field(..., description="ID SKU")
    warehouse_id: int = Field(..., description="ID склада (никогда не NULL)")
    source_location_id: Optional[int] = Field(
        None, description="Локация-источник (NULL допустим)"
    )
    destination_location_id: Optional[int] = Field(
        None, description="Локация-назначение (NULL допустим)"
    )
    status_id: int = Field(..., description="ID статуса")
    status_reason_id: int = Field(..., description="ID причины статуса")
    quantity: int = Field(..., gt=0, description="Количество (> 0)")
    event_time: datetime = Field(..., description="Время события (UTC)")
    planned_departure_time: datetime | None = Field(None, description="Плановое время отправки (nullable)")
    source_system: int = Field(..., description="Идентификатор исходной системы")


class AnalyticsIngestRequest(BaseModel):
    """
    Batch-запрос на ingest analytics-событий.

    - события обрабатываются независимо
    - частичный успех является нормой
    """

    events: List[AnalyticsEvent] = Field(
        ..., description="Список analytics-событий для ingestion"
    )
