# app/services/data_sources/postgres/connection.py
"""
PostgreSQL connection utilities (read-side).

ВАЖНО:
- этот модуль НЕ знает про FastAPI
- НЕ знает про ingest
- НЕ знает про selector
"""

import os
from typing import cast

import psycopg
from psycopg.rows import dict_row
from psycopg import Connection


def get_connection() -> Connection:
    """
    Создаёт новое подключение к PostgreSQL.

    Возвращает connection с row_factory=dict_row,
    чтобы cursor.fetchall() давал dict-подобные строки.
    """
    conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "logistics"),
        user=os.getenv("POSTGRES_USER", "logistics"),
        password=os.getenv("POSTGRES_PASSWORD", "logistics"),
        row_factory=dict_row,       # type: ignore[arg-type]
    )

    # Явно сообщаем типизатору, что это Connection с dict_row
    return cast(Connection, conn)