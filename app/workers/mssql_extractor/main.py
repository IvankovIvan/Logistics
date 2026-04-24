"""
MS SQL → Postgres ingestion worker (loop версия)

Теперь работает как сервис:
- постоянно читает новые события
- отправляет их в API
- двигает cursor
"""

from __future__ import annotations

import time

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


# интервал ожидания, если новых событий нет
SLEEP_SECONDS = 5


def chunked(batch, size):
    """
    Делит список batch на части фиксированного размера.
    """
    for i in range(0, len(batch), size):
        yield batch[i:i + size]


def run() -> None:
    """
    Основной цикл ingestion воркера.

    Логика:
    1. читаем cursor (последний обработанный event_id)
    2. берём новые события из MS SQL
    3. отправляем их в ingest API
    4. при успехе двигаем cursor
    """

    print("start app")
    # --- соединения ---
    # Postgres нужен для cursor
    pg_conn = get_pg_connection()

    # MS SQL — источник данных
    mssql_conn = get_mssql_connection()

    print("start while")
    # гарантируем, что строка cursor существует
    ensure_worker_row(pg_conn)

    print("mssql_extractor started")

    while True:
        try:
            print("start while")
            # --- читаем текущий cursor ---
            # ingest_cursor = последний обработанный event_id
            ingest_cursor = get_ingest_cursor(pg_conn)
            print("\ningest_cursor =", ingest_cursor)

            # --- читаем batch из MS SQL ---
            # берём только события с event_id > ingest_cursor
            batch = fetch_batch(mssql_conn, ingest_cursor, 1000)

            print("batch size =", len(batch))

            # --- если данных нет ---
            if not batch:
                print("no new events → sleep")
                time.sleep(SLEEP_SECONDS)
                continue

            print("sending batch...")

            # --- отправка в ingest API ---
            # API делает:
            # - idempotency
            # - запись в event store
            # важно: мы читаем большой batch из MS SQL,
            # но отправляем в API маленькими частями (chunk),
            # чтобы не перегружать Postgres и FastAPI
            for chunk in chunked(batch, 100):
                result = send_batch(chunk)
                print("chunk sent, size =", len(chunk))
            print("API result:", result)

            # --- обновление cursor ---
            # важно: cursor двигается ТОЛЬКО после успешной отправки

            event_ids: list[int] = []

            for item in batch:
                # event_id — ключ порядка событий
                value = item.get("event_id")

                if value is None:
                    raise RuntimeError("event_id отсутствует")

                # приводим к int (гарантия корректного типа)
                event_ids.append(int(value))

            # берём максимальный event_id из batch
            max_event_id = max(event_ids)

            # сохраняем новый cursor в Postgres
            update_ingest_cursor(pg_conn, max_event_id)

            print("cursor updated to", max_event_id)

        except Exception as e:
            # --- обработка ошибок ---
            # воркер НЕ должен падать
            print("ERROR:", e)

            # даём системе "остыть"
            time.sleep(3)


if __name__ == "__main__":
    run()