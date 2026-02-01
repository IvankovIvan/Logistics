# app/services/ingest/processor.py
from datetime import datetime
from typing import Set, List

from app.models.ingest import (
    IngestBatch,
    IngestBatchResult,
    IngestEventResult,
)
from app.services.ingest.rules import apply_event


# =====================================================
# In-memory idempotency store (TEMPORARY)
# =====================================================
# ⚠️ ВАЖНО:
# - используется только на этапе без БД
# - при рестарте приложения очищается
# - позже будет заменён на таблицу ingest_events
# =====================================================

_seen_event_ids: Set[str] = set()


def process_ingest_batch(batch: IngestBatch) -> IngestBatchResult:
    """
    Обрабатывает batch ingest-событий.

    Ответственность:
    - идемпотентность по event_id (in-memory)
    - вызов правил обработки события
    - сбор batch-результата

    НЕ делает:
    - запись в БД
    - транзакции
    - Celery
    """

    results: List[IngestEventResult] = []
    received_at = datetime.utcnow()

    for event in batch.events:
        # ---------------------------------------------
        # 1️⃣ Проверка идемпотентности
        # ---------------------------------------------
        if event.event_id in _seen_event_ids:
            results.append(
                IngestEventResult(
                    event_id=event.event_id,
                    status="duplicate",
                    reason="event_id already processed",
                )
            )
            continue

        # ---------------------------------------------
        # 2️⃣ Применение события (через rules)
        # ---------------------------------------------
        try:
            apply_event(event)
        except ValueError as exc:
            # Логически некорректное событие
            results.append(
                IngestEventResult(
                    event_id=event.event_id,
                    status="rejected",
                    reason=str(exc),
                )
            )
            # even rejected events are considered "seen"
            _seen_event_ids.add(event.event_id)
            continue

        # ---------------------------------------------
        # 3️⃣ Успешное применение
        # ---------------------------------------------
        _seen_event_ids.add(event.event_id)
        results.append(
            IngestEventResult(
                event_id=event.event_id,
                status="applied",
                reason=None,
            )
        )

    return IngestBatchResult(
        received_at=received_at,
        results=results,
    )