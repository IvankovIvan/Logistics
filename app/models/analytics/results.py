# app/models/analytics/results.py

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AnalyticsEventResult(BaseModel):
    """
    Результат обработки одного analytics-события.

    Статусы:
    - applied   — событие записано в event store
    - duplicate — событие уже существует (ON CONFLICT по operation_id + event_time)
    - rejected  — событие отклонено из-за ошибки валидации или БД
    """

    operation_id: int = Field(
        ..., description="operation_id исходного события"
    )
    status: Literal["applied", "duplicate", "rejected"] = Field(
        ..., description="Итог обработки события"
    )
    reason: Optional[str] = Field(
        None, description="Причина отказа (только для rejected)"
    )


class AnalyticsIngestResponse(BaseModel):
    """
    Результат обработки batch analytics ingest запроса.

    Batch никогда не считается целиком ошибочным,
    если хотя бы одно событие обработано успешно.
    """

    results: List[AnalyticsEventResult] = Field(
        ..., description="Результаты обработки каждого события"
    )
