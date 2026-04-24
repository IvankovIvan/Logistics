"""
Сохранение битых событий в DLQ (Dead Letter Queue).

DLQ (Dead Letter Queue)
сюда попадают события, которые не удалось обработать.
"""

from __future__ import annotations

import json

from app.workers.mssql_extractor.postgres import get_connection


def save_to_dlq(event: dict, error: str) -> None:
    """
    Сохраняет проблемное событие в analytics.ingest_dead_letter.
    """
    # DLQ (Dead Letter Queue)
    # сюда попадают события, которые не удалось обработать
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analytics.ingest_dead_letter (
                    source_event_id,
                    payload,
                    error
                )
                VALUES (%s, %s::jsonb, %s);
                """,
                (
                    event["event_id"],
                    json.dumps(event, default=str),
                    error,
                ),
            )
        conn.commit()
    finally:
        conn.close()
