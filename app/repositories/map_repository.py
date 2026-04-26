from app.services.db.connection import get_analytics_connection


SELECT_WAREHOUSES = """
SELECT
	warehouse_id,
	name,
	lat,
	lon
FROM analytics.warehouses
ORDER BY warehouse_id;
"""


SELECT_AGGREGATED_METRICS = """
WITH aggregated AS (
	SELECT
		warehouse_id,
		status_id,
		SUM(quantity) AS total_quantity
	FROM analytics.current_batch_state
	GROUP BY
		warehouse_id,
		status_id
)
SELECT
	warehouse_id,
	status_id,
	total_quantity,
	SUM(total_quantity) OVER (
		PARTITION BY warehouse_id
	) AS warehouse_total_quantity
FROM aggregated
ORDER BY
	warehouse_id,
	status_id;
"""


def fetch_warehouses():
	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(SELECT_WAREHOUSES)
			return cur.fetchall()


def fetch_warehouse_metrics():
	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(SELECT_AGGREGATED_METRICS)
			return cur.fetchall()
