# app/services/ingest/models.py
# Контракт ingest (Pydantic)

from datetime import datetime
from typing import Any, Literal, List
from pydantic import BaseModel, Field


class IngestEvent(BaseModel):
    event_id: str = Field(..., description="Уникальный ID события (идемпотентность)")
    event_time: datetime = Field(..., description="Время события (UTC, секунды)")
    entity_type: Literal["warehouse", "shipment"]
    payload: dict[str, Any]


class IngestBatch(BaseModel):
    events: List[IngestEvent]