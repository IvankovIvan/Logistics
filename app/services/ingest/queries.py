# app/services/ingest/queries.py

INSERT_INGEST_EVENT = """
INSERT INTO ingest_events (event_id, entity_type, entity_id, event_time)
VALUES (%(event_id)s, %(entity_type)s, %(entity_id)s, %(event_time)s)
ON CONFLICT (event_id) DO NOTHING;
"""

UPSERT_WAREHOUSE = """
INSERT INTO warehouses_current (
    id,
    name,
    status,
    location,
    last_event_time
)
VALUES (
    %(id)s,
    %(name)s,
    %(status)s,
    ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
    %(event_time)s
)
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    status = EXCLUDED.status,
    location = EXCLUDED.location,
    last_event_time = EXCLUDED.last_event_time,
    updated_at = now()
WHERE warehouses_current.last_event_time <= EXCLUDED.last_event_time;
"""


UPSERT_SHIPMENT = """
INSERT INTO shipments_current (
    id,
    from_node,
    to_node,
    status,
    last_event_time
)
VALUES (
    %(id)s,
    %(from_node)s,
    %(to_node)s,
    %(status)s,
    %(event_time)s
)
ON CONFLICT (id) DO UPDATE
SET
    from_node = EXCLUDED.from_node,
    to_node = EXCLUDED.to_node,
    status = EXCLUDED.status,
    last_event_time = EXCLUDED.last_event_time,
    updated_at = now()
WHERE shipments_current.last_event_time <= EXCLUDED.last_event_time;
"""