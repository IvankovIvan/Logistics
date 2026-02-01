# app/services/data_sources/postgres/queries.py
"""
SQL queries for read-side (current-state only).

ВАЖНО:
- только SELECT
- никакой логики
- никакого ingest
"""

WAREHOUSES_CURRENT = """
SELECT
    id,
    name,
    status,
    ST_X(location) AS lon,
    ST_Y(location) AS lat
FROM warehouses_current;
"""

SHIPMENTS_CURRENT = """
SELECT
    id,
    from_node,
    to_node,
    status
FROM shipments_current;
"""

LAST_UPDATED = """
SELECT
    GREATEST(
        COALESCE((SELECT MAX(updated_at) FROM warehouses_current), 'epoch'),
        COALESCE((SELECT MAX(updated_at) FROM shipments_current), 'epoch')
    ) AS last_updated;
"""