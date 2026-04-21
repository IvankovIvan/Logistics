# app/services/analytics_ingest/service.py
"""
Service-слой analytics ingest.

=== ЧТО ДЕЛАЕТ ===
Принимает список событий и записывает их в event store (inventory_status_events). 

=== КЛЮЧЕВАЯ ИДЕЯ ===

Каждое событие обрабатывается независимо через SAVEPOINT. 
Это позволяет:
- не ронять весь batch из-за одного события
- сохранить консистентность данных

=== ИНВАРИАНТЫ ===

- НЕ знает про FastAPI
- пишет ТОЛЬКО в event_table
- snapshot НЕ трогает
- использует только INSERT (append-only модель)
- идемпотентность обеспечивается на уровне БД через ON CONFLICT по operation_id + event_time
"""

from typing import Any, Mapping, cast

import logging
from typing import List

from psycopg import sql

from app.models.analytics.events import AnalyticsEvent
from app.models.analytics.results import AnalyticsEventResult, AnalyticsIngestResponse
from app.services.analytics_ingest.connection import get_analytics_connection
from app.services.analytics_ingest.queries import (
    CHECK_EVENT_TIME_RANGE,
    CREATE_MONTH_PARTITION,
    INSERT_ANALYTICS_EVENT,
)


LOGGER = logging.getLogger(__name__)


def ingest_analytics_events(events: List[AnalyticsEvent]) -> AnalyticsIngestResponse:
    """
    Основной метод ingest.
    Записывает список analytics-событий в event store.

    Для каждого события:
    - выполняет INSERT ... ON CONFLICT DO NOTHING в отдельном SAVEPOINT
    - rowcount == 1 → applied
    - rowcount == 0 → duplicate (conflict по operation_id + event_time)
    - исключение     → rejected (ROLLBACK TO SAVEPOINT, транзакция продолжается)

    === ПОВЕДЕНИЕ ===
    Для каждого события:
    1. Проверяем допустимый диапазон event_time
    2. Гарантируем наличие партиции
    3. Пытаемся вставить событие
    4. Фиксируем результат (applied / duplicate / rejected)

    === ВАЖНО ===
    Весь batch = одна транзакция
    Но каждое событие = отдельный SAVEPOINT

    Возвращает AnalyticsIngestResponse с результатом по каждому событию.    
    """

    results: List[AnalyticsEventResult] = []

    # Открываем соединение (одна транзакция на весь batch) 
    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            for event in events:
                # Создаём savepoint для изоляции ошибки конкретного события
                savepoint = f"sp_{event.operation_id}"

                try:
                    # --- 1. SAVEPOINT ---
                    # Позволяет откатить только текущее событие при ошибке, не влияя на остальные
                    cur.execute(
                        sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint))
                    )

                    # --- 2. Проверка диапазона времени ---
                    # Защита от:
                    # - слишком старых событий 
                    # - событий из будущего 
                    cur.execute(
                        CHECK_EVENT_TIME_RANGE,
                        {"event_time": event.event_time},
                    )
                    range_row = cast(Mapping[str, Any], cur.fetchone())

                    if range_row is None:
                        raise RuntimeError("event_time range check returned no rows")

                    is_in_range = bool(range_row["is_in_range"])

                    # Если событие вне диапазона → reject и продолжаем (не роняя транзакцию)
                    if not is_in_range:
                        cur.execute(
                            sql.SQL("RELEASE SAVEPOINT {}").format(
                                sql.Identifier(savepoint)
                            )
                        )
                        LOGGER.warning(
                            "Rejected analytics event out of range: operation_id=%s event_time=%s",
                            event.operation_id,
                            event.event_time,
                        )
                        results.append(
                            AnalyticsEventResult(
                                operation_id=event.operation_id,
                                status="rejected",
                                reason="event_time out of allowed range",
                            )
                        )
                        continue

                    # --- 3. Создание партиции ---
                    # Если партиции нет → создаётся динамически (до уровня месяца)
                    # Если есть → ничего не происходит (логируется в service.log)
                    cur.execute(
                        CREATE_MONTH_PARTITION,
                        {"event_time": event.event_time},
                    )
                    partition_row = cast(Mapping[str, Any], cur.fetchone())

                    # Если реально создали новую партицию → логируем (важно для мониторинга и отладки)
                    if partition_row is not None:
                        created_partition = partition_row["created_partition"]
                        if created_partition:
                            LOGGER.info(
                                "Created analytics partition: %s",
                                created_partition,
                            )
                    
                    # --- 4. INSERT события ---
                    # ON CONFLICT DO NOTHING → защита от дублей по operation_id + event_time
                    cur.execute(
                        INSERT_ANALYTICS_EVENT,
                        {
                            "batch_id": event.batch_id,
                            "order_id": event.order_id,
                            "sku_id": event.sku_id,
                            "warehouse_id": event.warehouse_id,
                            "source_location_id": event.source_location_id,
                            "destination_location_id": event.destination_location_id,
                            "status_id": event.status_id,
                            "status_reason_id": event.status_reason_id,
                            "quantity": event.quantity,
                            "event_time": event.event_time,
                            "source_system": event.source_system,
                            "operation_id": event.operation_id,
                        },
                    )

                    # --- 5. Проверка результата INSERT ---
                    if cur.rowcount == 1:
                        # Событие успешно вставлено → фиксируем результат и продолжаем
                        cur.execute(
                            sql.SQL("RELEASE SAVEPOINT {}").format(
                                sql.Identifier(savepoint)
                            )
                        )
                        results.append(
                            AnalyticsEventResult(
                                operation_id=event.operation_id,
                                status="applied",
                                reason=None,
                            )
                        )
                    else:
                        # Событие уже было (duplicate) → фиксируем результат и продолжаем (не роняя транзакцию)
                        # ON CONFLICT DO NOTHING — строка уже существует
                        cur.execute(
                            sql.SQL("RELEASE SAVEPOINT {}").format(
                                sql.Identifier(savepoint)
                            )
                        )
                        results.append(
                            AnalyticsEventResult(
                                operation_id=event.operation_id,
                                status="duplicate",
                                reason="conflict on operation_id + event_time",
                            )
                        )

                except Exception as exc:
                    # --- 6. Ошибка ---
                    # Откатываем ТОЛЬКО текущее событие, не влияя на остальные
                    # Транзакция продолжается, остальные события обрабатываются дальше
                    # Откатываем только текущее событие, транзакция продолжается
                    cur.execute(
                        sql.SQL("ROLLBACK TO SAVEPOINT {}").format(
                            sql.Identifier(savepoint)
                        )
                    )
                    cur.execute(
                        sql.SQL("RELEASE SAVEPOINT {}").format(
                            sql.Identifier(savepoint)
                        )
                    )
                    results.append(
                        AnalyticsEventResult(
                            operation_id=event.operation_id,
                            status="rejected",
                            reason=str(exc),
                        )
                    )
        
        # --- 7. Commit всей транзакции ---
        conn.commit()

    return AnalyticsIngestResponse(results=results)
