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
from collections.abc import Sequence
from typing import Mapping

import requests


# используем Sequence и Mapping вместо list/dict
# чтобы поддерживать TypedDict (EventRow)
def send_batch(batch: Sequence[Mapping[str, object]]) -> object:
    """
    Отправляет batch событий в ingest API.

    batch — список событий из MS SQL,
    которые нужно передать в систему аналитики.
    """
    url = os.getenv("INGEST_API_URL")

    if not url:
        raise RuntimeError("INGEST_API_URL не задан")

    # timeout=30 защищает от зависания при недоступном API:
    # без таймаута запрос может ждать бесконечно и заблокировать воркер.
    response = requests.post(
        url,
        json={"events": batch},
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"API error: {response.status_code} {response.text}"
        )

    return response.json()
