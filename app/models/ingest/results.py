# app/models/ingest/results.py
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class IngestEventResult(BaseModel):
    """
    Результат обработки одного ingest-события.

    Статусы:
    - applied   — событие применено к current-state
    - duplicate — событие уже было обработано (идемпотентность)
    - rejected  — событие отклонено (валидация/логические причины)
    """

    event_id: str = Field(
        ...,
        description="event_id исходного ingest-события"
    )

    status: Literal["applied", "duplicate", "rejected"] = Field(
        ...,
        description="Итог обработки события"
    )

    reason: Optional[str] = Field(
        None,
        description="Причина отказа или пояснение (только для rejected)"
    )


class IngestBatchResult(BaseModel):
    """
    Результат обработки batch ingest-запроса.

    Важно:
    - batch никогда не считается целиком ошибочным,
      если хотя бы одно событие обработано.
    """

    received_at: datetime = Field(
        ...,
        description="Время приёма batch сервером"
    )

    results: List[IngestEventResult] = Field(
        ...,
        description="Результаты обработки каждого события"
    )