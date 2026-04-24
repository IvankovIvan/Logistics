# /opt/Logistics/app/workers/mssql_extractor/main.py
"""
Тестовый модуль: связка Postgres cursor и MS SQL fetch_batch.

Назначение:
- убедиться, что ingest_cursor корректно читается из Postgres;
- убедиться, что MS SQL возвращает только новые события начиная с cursor;
- проверить, что процедура `sp_get_events_after_id` доступна и работает.
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
)


if __name__ == "__main__":
    # Подключаемся к Postgres и инициализируем строку cursor.
    pg_conn = get_pg_connection()

    # Если воркер запускается впервые — создаёт строку с last_processed_event_id = 0.
    ensure_worker_row(pg_conn)

    # Читаем текущую позицию cursor.
    # ingest_cursor — это last_processed_event_id: событие с этим id уже обработано.
    # Процедура вернёт только события с event_id > ingest_cursor,
    # чтобы не читать уже обработанные данные повторно.
    ingest_cursor = get_ingest_cursor(pg_conn)
    print("ingest_cursor =", ingest_cursor)

    # Подключаемся к MS SQL и читаем batch новых событий.
    mssql_conn = get_mssql_connection()

    # fetch_batch передаёт ingest_cursor в процедуру как нижнюю границу:
    # возвращаются только события с event_id > ingest_cursor.
    # Это гарантирует, что каждое событие обрабатывается ровно один раз.
    batch = fetch_batch(mssql_conn, ingest_cursor, 10)

    print("batch size =", len(batch))
    for item in batch:
        print(item)

    mssql_conn.close()
    pg_conn.close()
