"""
Тестовый модуль: связка Postgres cursor + MS SQL + Ingest API.

Назначение:
- читаем ingest_cursor из Postgres
- читаем batch из MS SQL (только новые события)
- отправляем batch в ingest API
- при успехе двигаем cursor вперёд
"""

from __future__ import annotations

from app.workers.mssql_extractor.mssql import (
    fetch_batch,
    get_connection as get_mssql_connection,
)
from app.workers.mssql_extractor.postgres import (
    ensure_worker_row,
    get_connection as get_pg_connection,
    get_ingest_cursor,
    update_ingest_cursor,
)
from app.workers.mssql_extractor.api import send_batch


if __name__ == "__main__":
    # --- Postgres (cursor) ---
    pg_conn = get_pg_connection()

    # если первый запуск — создаём строку cursor
    ensure_worker_row(pg_conn)

    # читаем текущий cursor
    ingest_cursor = get_ingest_cursor(pg_conn)
    print("ingest_cursor =", ingest_cursor)

    # --- MS SQL (source) ---
    mssql_conn = get_mssql_connection()

    # читаем только новые события:
    # event_id > ingest_cursor
    batch = fetch_batch(mssql_conn, ingest_cursor, 10)

    print("batch size =", len(batch))

    # чтобы не заспамить лог — выводим первые 5
    for item in batch[:5]:
        print(item)

    # --- если есть данные → отправляем ---
    if batch:
        print("sending batch to API...")

        result = send_batch(batch)

        print("API result:", result)

        # --- обновляем cursor ---
        # Pylance-safe версия (без cast, с явной типизацией)
        event_ids: list[int] = []

        for item in batch:
            value = item.get("event_id")

            if value is None:
                raise RuntimeError("event_id отсутствует в batch")

            event_id = int(value)
            event_ids.append(event_id)

        max_event_id = max(event_ids)

        update_ingest_cursor(pg_conn, max_event_id)

        print("cursor updated to", max_event_id)
    else:
        print("no new events")

    # --- закрываем соединения ---
    mssql_conn.close()
    pg_conn.close()