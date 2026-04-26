# app/services/analytics_ingest/service.py
"""
Service-слой analytics ingest.
🔥 Вся логика в 5 строках
events →
    filter →
    group months →
    create partitions →
    try batch insert →
        ok → fast
        fail → fallback

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

import logging
from datetime import datetime, timezone
from typing import List, Mapping, Any, cast

from psycopg import sql

from app.models.analytics.events import AnalyticsEvent
from app.models.analytics.results import AnalyticsEventResult, AnalyticsIngestResponse
from app.repositories.ingest_repository import (
    create_partition,
    insert_event,
)
from app.services.db.connection import get_analytics_connection


LOGGER = logging.getLogger(__name__)

EVENT_INSERT_COLUMNS = (
    "batch_id",
    "order_id",
    "sku_id",
    "warehouse_id",
    "source_location_id",
    "destination_location_id",
    "status_id",
    "status_reason_id",
    "quantity",
    "event_time",
    "planned_departure_time",
    "source_system",
    "operation_id",
)


def _add_months(dt: datetime, months: int) -> datetime:
    """
    Сдвигает datetime на N календарных месяцев. 
    ⚠️ Почему не timedelta:
    - timedelta не умеет месяцы (они разной длины) 
    - здесь делаем ручной расчёт месяцев и лет
    ⚠️ Важно:
    - сохраняется timezone (UTC) 
    """
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    return dt.replace(year=year, month=month)


def _month_start_utc(dt: datetime) -> datetime:
    """
    Приводит дату к началу месяца (UTC). 
    Пример:
    2026-03-15 → 2026-03-01 00:00:00 
    Нужно для:
    - определения partition для события
    - оптимизации запросов к event store (по партициям)
    """
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _event_params(event: AnalyticsEvent) -> dict[str, object]:
    """
    Преобразует событие в словарь параметров для SQL. 
    Используется:
    - в fallback insert
    - в batch insert builder
    """
    return {
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
        "planned_departure_time": event.planned_departure_time,
        "source_system": event.source_system,
        "operation_id": event.operation_id,
    }


def _build_batch_insert_query(events_count: int) -> sql.Composed:
    """
    Динамически строит batch INSERT запрос. 
    
    Пример:
    INSERT INTO table (...) VALUES

        (%(batch_id_0)s, ...),

        (%(batch_id_1)s, ...)

    Почему сложно:
    - psycopg не умеет batch insert "из коробки"
    - нужно вручную генерировать placeholders
    - важно сохранить ON CONFLICT для идемпотентности
    """
    values_sql = sql.SQL(", ").join(
        sql.SQL("(")
        + sql.SQL(", ").join(
            sql.Placeholder(f"{col}_{idx}") for col in EVENT_INSERT_COLUMNS
        )
        + sql.SQL(")")
        for idx in range(events_count)
    )

    return sql.SQL(
        """
        INSERT INTO analytics.inventory_status_events (
            batch_id,
            order_id,
            sku_id,
            warehouse_id,
            source_location_id,
            destination_location_id,
            status_id,
            status_reason_id,
            quantity,
            event_time,
            planned_departure_time,
            source_system,
            operation_id
        )
        VALUES {values_sql}
        ON CONFLICT (operation_id, event_time) DO NOTHING
        RETURNING operation_id;
        """
    ).format(values_sql=values_sql)


def _build_batch_params(events: list[AnalyticsEvent]) -> dict[str, object]:
    """
    Формирует параметры для batch INSERT. 
    Превращает список событий в:
    col_0, col_1, col_2 ...
    Это нужно потому что:
    - SQL placeholders уникальны для каждой строки в batch insert
    - мы не можем использовать один и тот же placeholder для всех строк
    - нужно вручную пронумеровать параметры для каждого события
    """
    params: dict[str, object] = {}

    for idx, event in enumerate(events):
        event_params = _event_params(event)
        for col in EVENT_INSERT_COLUMNS:
            params[f"{col}_{idx}"] = event_params[col]

    return params


def _insert_events_fallback_per_event(
    cur,
    events: list[AnalyticsEvent],
    results: list[AnalyticsEventResult],
) -> None:
    """
    Fallback путь (медленный, но надёжный). 
    Используется если batch insert упал. 
    Гарантии:
    - каждое событие обрабатывается независимо через SAVEPOINT
    - batch не ломается из-за одного проблемного события
    - сохраняется идемпотентность через ON CONFLICT 
    - результат по каждому событию фиксируется (applied / duplicate / rejected)
     ⚠️ Важно:
    - этот код должен работать даже если структура таблицы изменилась (по одной строке за раз)
    - поэтому мы используем отдельный INSERT для каждого события, а не batch insert
    """
    for event in events:
        savepoint = f"sp_{event.operation_id}"

        try:
            cur.execute(
                sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint))
            )

            inserted_row = insert_event(_event_params(event), cur)

            if inserted_row is not None:
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

    #задаём допустимое окно для event_time (от -6 месяцев до +1 месяца от текущей даты)
    now_utc = datetime.now(timezone.utc)
    min_time = _add_months(now_utc, -6)
    max_time = _add_months(now_utc, 1)

    valid_events: list[AnalyticsEvent] = []
    months: set[datetime] = set()

    for event in events:
        event_time_utc = event.event_time.astimezone(timezone.utc)

        if event_time_utc < min_time or event_time_utc > max_time:
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

        valid_events.append(event)
        months.add(_month_start_utc(event_time_utc))

    # Открываем соединение (одна транзакция на весь batch)
    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            for month_start in sorted(months):
                partition_row = cast(
                    Mapping[str, Any] | None,
                    create_partition(month_start, cur),
                )
                if partition_row is not None:
                    created_partition = partition_row["created_partition"]
                    if created_partition:
                        LOGGER.info(
                            "Created analytics partition: %s",
                            created_partition,
                        )

            if valid_events:
                LOGGER.info("Analytics ingest batch insert attempt: batch_size=%s", len(valid_events))

                try:
                    batch_query = _build_batch_insert_query(len(valid_events))
                    batch_params = _build_batch_params(valid_events)
                    cur.execute(batch_query, batch_params)
                    inserted_rows = cast(list[Mapping[str, Any]], cur.fetchall())
                    inserted_operation_ids = {
                        int(row["operation_id"]) for row in inserted_rows
                    }

                    for event in valid_events:
                        if event.operation_id in inserted_operation_ids:
                            results.append(
                                AnalyticsEventResult(
                                    operation_id=event.operation_id,
                                    status="applied",
                                    reason=None,
                                )
                            )
                        else:
                            results.append(
                                AnalyticsEventResult(
                                    operation_id=event.operation_id,
                                    status="duplicate",
                                    reason="conflict on operation_id + event_time",
                                )
                            )
                except Exception:
                    LOGGER.exception(
                        "Analytics ingest batch insert failed, fallback triggered: batch_size=%s",
                        len(valid_events),
                    )
                    _insert_events_fallback_per_event(cur, valid_events, results)
        
                # --- 6. Commit всей транзакции ---
        conn.commit()

    return AnalyticsIngestResponse(results=results)
