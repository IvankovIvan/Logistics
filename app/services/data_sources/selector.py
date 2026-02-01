# app/services/data_sources/selector.py
import os

from app.services.data_sources.base import CurrentStateDataSource
from app.services.data_sources.fake import FakeDataSource
from app.services.data_sources.ingest_memory import InMemoryIngestDataSource


def get_current_state_data_source() -> CurrentStateDataSource:
    """
    Возвращает источник current-state данных для карты.

    Выбор осуществляется через переменную окружения:

    DATA_SOURCE_MODE:
      - fake        (default) — FAKE данные
      - ingest_mem  — in-memory ingest state
    """

    mode = os.getenv("DATA_SOURCE_MODE", "fake")

    if mode == "ingest_mem":
        return InMemoryIngestDataSource()

    # default / fallback
    return FakeDataSource()