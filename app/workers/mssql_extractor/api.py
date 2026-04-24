# app/workers/mssql_extractor/api.py
"""
Утилита отправки событий в ingest API.

ingest API — это HTTP-эндпоинт системы аналитики, который принимает события
из внешних источников (в данном случае из MS SQL) и сохраняет их в analytics-db.

Отправляем события батчом, а не по одному, чтобы снизить накладные расходы
на HTTP-запросы и уменьшить нагрузку на API при большом потоке событий.
"""

from __future__ import annotations

import os
import time
from collections.abc import Sequence
from typing import List, Mapping, Optional, TypedDict

import requests
from app.workers.mssql_extractor.config import (
    HTTP_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)


# настройки retry и timeout управляются через config.py


class ResultItem(TypedDict):
    operation_id: int
    status: str
    reason: Optional[str]


class SendBatchResponse(TypedDict):
    results: List[ResultItem]


# используем Sequence и Mapping вместо list/dict
# чтобы поддерживать TypedDict (EventRow)
# типизация ответа API нужна для корректной работы Pylance
# и безопасного доступа к result["results"]
def send_batch(batch: Sequence[Mapping[str, object]]) -> SendBatchResponse:
    """
    Отправляет batch событий в ingest API.

    batch — список событий из MS SQL,
    которые нужно передать в систему аналитики.

    retry нужен для защиты от временных ошибок сети или API.
    cursor не должен двигаться, если send_batch не завершился успешно.
    """
    url = os.getenv("INGEST_API_URL")

    if not url:
        raise RuntimeError("INGEST_API_URL не задан")

    for attempt in range(MAX_RETRIES):
        try:
            # timeout=30 защищает от зависания при недоступном API:
            # без таймаута запрос может ждать бесконечно и заблокировать воркер.
            response = requests.post(
                url,
                json={"events": batch},
                timeout=HTTP_TIMEOUT,
            )

            # HTTP 5xx — ошибка сервера → retry
            if response.status_code >= 500:
                raise RuntimeError(f"server error: {response.status_code}")

            # HTTP 4xx — логическая ошибка → НЕ retry
            if response.status_code != 200:
                raise RuntimeError(
                    f"API error: {response.status_code} {response.text}"
                )

            return response.json()

        except Exception as e:
            # retry при любой ошибке (timeout, сетевая, 5xx)
            print(f"retry {attempt + 1}/{MAX_RETRIES} error:", e)

            if attempt == MAX_RETRIES - 1:
                raise

            time.sleep(RETRY_DELAY)

    raise RuntimeError("send_batch завершился без результата")
