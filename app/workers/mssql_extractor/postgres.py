"""
Утилиты для хранения ingest_cursor воркера mssql_extractor в Postgres.

ingest_cursor — это последнее успешно обработанное событие.
Он нужен, чтобы после перезапуска воркер продолжал чтение не с начала,
а с последней подтверждённой позиции.

Курсор хранится в Postgres, потому что это общее и устойчивое хранилище:
значение не теряется при рестарте контейнера и доступно между запусками воркера.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import cast

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row


WORKER_NAME = "mssql_extractor"


def get_connection() -> Connection:
    """
    Возвращает подключение к analytics Postgres.

    Подключение берётся из env:
    - ANALYTICS_POSTGRES_HOST
    - ANALYTICS_POSTGRES_PORT
    - ANALYTICS_POSTGRES_DB
    - ANALYTICS_POSTGRES_USER
    - ANALYTICS_POSTGRES_PASSWORD
    """
    conn = psycopg.connect(
        host=os.getenv("ANALYTICS_POSTGRES_HOST", "analytics-db"),
        port=int(os.getenv("ANALYTICS_POSTGRES_PORT", "5432")),
        dbname=os.getenv("ANALYTICS_POSTGRES_DB", "analytics"),
        user=os.getenv("ANALYTICS_POSTGRES_USER", "analytics"),
        password=os.getenv("ANALYTICS_POSTGRES_PASSWORD", "analytics"),
        row_factory=dict_row,  # type: ignore[arg-type]
    )
    return cast(Connection, conn)


def get_ingest_cursor(conn: Connection) -> int:
    """
    Читает ingest_cursor из analytics.worker_state.

    Возвращает last_processed_event_id для worker_name = 'mssql_extractor'.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT last_processed_event_id
            FROM analytics.worker_state
            WHERE worker_name = %s;
            """,
            (WORKER_NAME,),
        )
        row = cur.fetchone()

    if row is None:
        raise RuntimeError("worker_state row not found")

    # cast нужен только для Pylance: в runtime row уже dict-подобный
    # объект благодаря row_factory=dict_row.
    row = cast(Mapping[str, object], row)

    return int(cast(int | str, row["last_processed_event_id"]))


def ensure_worker_row(conn: Connection) -> None:
    """
    Гарантирует наличие строки состояния воркера в analytics.worker_state.

    Если строки для mssql_extractor ещё нет, создаёт её с начальным
    last_processed_event_id = 0.

    commit выполняется только если действительно был insert.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM analytics.worker_state
            WHERE worker_name = %s;
            """,
            (WORKER_NAME,),
        )
        row = cur.fetchone()

        if row is not None:
            return

        cur.execute(
            """
            INSERT INTO analytics.worker_state (
                worker_name,
                last_processed_event_id
            )
            VALUES (%s, %s);
            """,
            (WORKER_NAME, 0),
        )

    conn.commit()


def update_ingest_cursor(conn: Connection, new_cursor: int) -> None:
    """
    Обновляет ingest_cursor в analytics.worker_state.

    new_cursor — это максимальный event_id,
    который успешно обработан и отправлен в систему.
    """
    with conn.cursor() as cur:
        # cursor обновляется только после успешного batch
        cur.execute(
            """
            UPDATE analytics.worker_state
            SET last_processed_event_id = %s
            WHERE worker_name = %s;
            """,
            (new_cursor, WORKER_NAME),
        )

    conn.commit()