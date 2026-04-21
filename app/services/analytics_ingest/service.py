# app/services/analytics_ingest/service.py
"""
Service-слой analytics ingest.

Инварианты:
- НЕ знает про FastAPI
- пишет ТОЛЬКО в analytics.inventory_status_events
- НЕ пишет в snapshot (current_batch_state)
- НЕ делает UPSERT — только INSERT ... ON CONFLICT DO NOTHING
- каждое событие обрабатывается в отдельном SAVEPOINT
- batch не падает целиком при ошибке отдельного события
"""

from typing import List

from psycopg import sql

from app.models.analytics.events import AnalyticsEvent
from app.models.analytics.results import AnalyticsEventResult, AnalyticsIngestResponse
from app.services.analytics_ingest.connection import get_analytics_connection
from app.services.analytics_ingest.queries import INSERT_ANALYTICS_EVENT


def ingest_analytics_events(events: List[AnalyticsEvent]) -> AnalyticsIngestResponse:
    """
    Записывает список analytics-событий в event store.

    Для каждого события:
    - выполняет INSERT ... ON CONFLICT DO NOTHING в отдельном SAVEPOINT
    - rowcount == 1 → applied
    - rowcount == 0 → duplicate (conflict по operation_id + event_time)
    - исключение     → rejected (ROLLBACK TO SAVEPOINT, транзакция продолжается)

    Возвращает AnalyticsIngestResponse с результатом по каждому событию.
    """

    results: List[AnalyticsEventResult] = []

    with get_analytics_connection() as conn:
        with conn.cursor() as cur:
            for event in events:
                savepoint = f"sp_{event.operation_id}"

                try:
                    cur.execute(
                        sql.SQL("SAVEPOINT {}").format(sql.Identifier(savepoint))
                    )

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

                    if cur.rowcount == 1:
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

        conn.commit()

    return AnalyticsIngestResponse(results=results)
