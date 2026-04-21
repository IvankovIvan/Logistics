# app/services/analytics_ingest/connection.py
"""
PostgreSQL connection для analytics-db.

ВАЖНО:
- отдельное подключение от project1-db (logistics)
- НЕ знает про FastAPI, ingest и map
- используется только analytics_ingest service
"""

import os
from typing import cast

import psycopg
from psycopg.rows import dict_row
from psycopg import Connection


def get_analytics_connection() -> Connection:
    """
    Создаёт подключение к analytics-db.

    Переменные окружения:
    - ANALYTICS_HOST     (default: analytics-db)
    - ANALYTICS_PORT     (default: 5432)
    - ANALYTICS_DB       (default: analytics)
    - ANALYTICS_USER     (default: analytics)
    - ANALYTICS_PASSWORD (default: analytics)
    """
    conn = psycopg.connect(
        host=os.getenv("ANALYTICS_HOST", "analytics-db"),
        port=int(os.getenv("ANALYTICS_PORT", "5432")),
        dbname=os.getenv("ANALYTICS_DB", "analytics"),
        user=os.getenv("ANALYTICS_USER", "analytics"),
        password=os.getenv("ANALYTICS_PASSWORD", "analytics"),
        row_factory=dict_row,  # type: ignore[arg-type]
    )

    return cast(Connection, conn)
