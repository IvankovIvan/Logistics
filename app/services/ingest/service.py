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
    """
    received = 0
    inserted = 0
    applied = 0

    applied_event_ids: list[str] = []

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

                # enum → value (строка)
                if "status" in payload and hasattr(payload["status"], "value"):
                    payload["status"] = payload["status"].value

                # -------------------------------------------------
                # 1) Idempotency
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
                    continue

                inserted += 1

                # -------------------------------------------------
                # 2) Apply current-state
                # -------------------------------------------------
                if ev.entity_type == "warehouse":
                    cur.execute(
                        UPSERT_WAREHOUSE,
                        {
                            "id": payload["id"],
                            "name": payload["name"],
                            "status": payload["status"],
                            "lon": payload["lon"],
                            "lat": payload["lat"],
                            "event_time": ev.event_time,
                        },
                    )
                    applied += cur.rowcount
                    applied_event_ids.append(ev.event_id)

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
                    applied += cur.rowcount
                    applied_event_ids.append(ev.event_id)

                else:
                    # защита от мусора
                    continue

        conn.commit()

    return {
        "received": received,
        "inserted": inserted,
        "applied": applied,
        "applied_event_ids": applied_event_ids,
    }