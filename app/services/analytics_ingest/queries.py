# app/services/analytics_ingest/queries.py
"""
SQL-запросы для analytics event store.

ВАЖНО:
- только INSERT
- никаких UPDATE / DELETE / SELECT
- append-only семантика
"""

INSERT_ANALYTICS_EVENT = """
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
    source_system,
    operation_id
)
VALUES (
    %(batch_id)s,
    %(order_id)s,
    %(sku_id)s,
    %(warehouse_id)s,
    %(source_location_id)s,
    %(destination_location_id)s,
    %(status_id)s,
    %(status_reason_id)s,
    %(quantity)s,
    %(event_time)s,
    %(source_system)s,
    %(operation_id)s
)
ON CONFLICT (operation_id, event_time) DO NOTHING;
"""


CHECK_EVENT_TIME_RANGE = """
SELECT (
    %(event_time)s >= now() - interval '6 months'
    AND %(event_time)s <= now() + interval '1 month'
) AS is_in_range;
"""


CREATE_MONTH_PARTITION = """
SELECT analytics.create_month_partition(%(event_time)s) AS created_partition;
"""
