# app/services/ingest/service.py

from typing import Iterable

from app.services.data_sources.postgres.connection import get_connection
from app.services.ingest.queries import (
    INSERT_INGEST_EVENT,
    UPSERT_WAREHOUSE,
    UPSERT_SHIPMENT,
)


def ingest_events(events: Iterable):
    """
    Ingest pipeline (sync).

    Инварианты:
    - ingest-service НЕ знает про FastAPI
    - payload приводится к dict[str, primitive]
    - enum → value
    - applied возвращается ТОЛЬКО если current-state реально изменён
    """

    received = 0
    inserted = 0
    applied = 0

    applied_event_ids: list[str] = []
    event_results: list[dict[str, object | None]] = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            for ev in events:
                received += 1

                # -------------------------------------------------
                # Payload normalization
                # -------------------------------------------------
                if hasattr(ev.payload, "model_dump"):
                    payload = ev.payload.model_dump()
                else:
                    payload = dict(ev.payload)

                # enum → value
                if "status" in payload and hasattr(payload["status"], "value"):
                    payload["status"] = payload["status"].value

                # -------------------------------------------------
                # 1) Idempotency (event_id)
                # -------------------------------------------------
                cur.execute(
                    INSERT_INGEST_EVENT,
                    {
                        "event_id": ev.event_id,
                        "entity_type": ev.entity_type,
                        "entity_id": payload.get("id"),
                        "event_time": ev.event_time,
                    },
                )

                if cur.rowcount == 0:
                    # event_id уже был — это duplicate
                    event_results.append(
                        {
                            "event_id": ev.event_id,
                            "status": "duplicate",
                            "reason": "event_id already processed",
                        }
                    )
                    continue

                inserted += 1

                # -------------------------------------------------
                # 2) Apply current-state
                # -------------------------------------------------
                if ev.entity_type == "warehouse":
                    if "quantity" not in payload:
                        event_results.append(
                            {
                                "event_id": ev.event_id,
                                "status": "rejected",
                                "reason": "warehouse payload missing quantity",
                            }
                        )
                        continue
                    cur.execute(
                        UPSERT_WAREHOUSE,
                        {
                            "id": payload["id"],
                            "name": payload["name"],
                            "status": payload["status"],
                            "lon": payload["lon"],
                            "lat": payload["lat"],
                            "quantity": payload["quantity"],
                            "event_time": ev.event_time,
                        },
                    )
                    applied_rowcount = cur.rowcount

                elif ev.entity_type == "shipment":
                    cur.execute(
                        UPSERT_SHIPMENT,
                        {
                            "id": payload["id"],
                            "from_node": payload["from_warehouse_id"],
                            "to_node": payload["to_warehouse_id"],
                            "status": payload["status"],
                            "event_time": ev.event_time,
                        },
                    )
                    applied_rowcount = cur.rowcount

                else:
                    # неизвестный entity_type → rejected
                    event_results.append(
                        {
                            "event_id": ev.event_id,
                            "status": "rejected",
                            "reason": "unsupported entity_type",
                        }
                    )
                    continue

                # -------------------------------------------------
                # 3) Result classification
                # -------------------------------------------------
                # UPSERT может не примениться, если событие устарело
                # (WHERE last_event_time <= EXCLUDED.last_event_time)
                if applied_rowcount > 0:
                    applied += applied_rowcount
                    applied_event_ids.append(ev.event_id)
                    event_results.append(
                        {
                            "event_id": ev.event_id,
                            "status": "applied",
                            "reason": None,
                        }
                    )
                else:
                    # корректный stale
                    event_results.append(
                        {
                            "event_id": ev.event_id,
                            "status": "stale",
                            "reason": "stale event_time",
                        }
                    )

        conn.commit()

    return {
        "received": received,
        "inserted": inserted,
        "applied": applied,
        "applied_event_ids": applied_event_ids,
        "event_results": event_results,
    }
