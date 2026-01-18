from typing import Dict

from pydantic import BaseModel, Field


class ShipmentsNow(BaseModel):
    """
    Витрина перевозок на сейчас.

    Агрегированное текущее состояние перевозок
    без хранения истории.
    """
    total: int = Field(..., description="Общее количество перевозок")
    by_status: Dict[str, int] = Field(
        ...,
        description="Количество перевозок по каждому статусу",
    )