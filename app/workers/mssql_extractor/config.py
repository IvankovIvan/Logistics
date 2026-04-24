"""
Конфигурация mssql_extractor.

Все настройки вынесены в env,
чтобы можно было управлять поведением воркера без изменения кода.
"""

from __future__ import annotations

import os


def get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


# --- batch ---
BATCH_SIZE = get_int("MSSQL_BATCH_SIZE", 1000)
CHUNK_SIZE = get_int("MSSQL_CHUNK_SIZE", 100)

# --- loop ---
SLEEP_SECONDS = get_int("MSSQL_SLEEP_SECONDS", 5)

# --- retry ---
MAX_RETRIES = get_int("MSSQL_MAX_RETRIES", 3)
RETRY_DELAY = get_int("MSSQL_RETRY_DELAY", 2)

# --- http ---
HTTP_TIMEOUT = get_int("MSSQL_HTTP_TIMEOUT", 30)
