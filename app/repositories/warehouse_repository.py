from app.services.db.connection import get_analytics_connection


def fetch_warehouse_metadata(warehouse_id: int):
	query = """
	SELECT
		w.warehouse_id,
		w.name,
		c.name AS city,
		wt.name AS warehouse_type
	FROM analytics.warehouses w
	JOIN analytics.cities c
		ON c.city_id = w.city_id
	JOIN analytics.warehouse_types wt
		ON wt.warehouse_type_id = w.warehouse_type_id
	WHERE w.warehouse_id = %(warehouse_id)s;
	"""

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query, {"warehouse_id": warehouse_id})
			return cur.fetchone()


def fetch_warehouse_metrics(warehouse_id: int):
	query = """
	WITH base AS (
		SELECT
			status_id,
			quantity
		FROM analytics.current_batch_state
		WHERE warehouse_id = %(warehouse_id)s
	),
	totals AS (
		SELECT
			COUNT(*) AS total_count,
			SUM(quantity) AS total_sum
		FROM base
	),
	by_status AS (
		SELECT
			b.status_id,
			COUNT(*) AS count,
			SUM(b.quantity) AS sum
		FROM base b
		GROUP BY b.status_id
	)
	SELECT
		bs.status_id,
		d.description AS status_text,
		bs.count,
		bs.sum,
		t.total_count,
		t.total_sum
	FROM by_status bs
	LEFT JOIN analytics.status_dict d
		ON d.status_id = bs.status_id
	CROSS JOIN totals t
	ORDER BY bs.status_id ASC;
	"""

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query, {"warehouse_id": warehouse_id})
			return cur.fetchall()


def fetch_warehouse_batches(warehouse_id: int):
	query = """
	SELECT
		batch_id,
		status_id,
		quantity,
		warehouse_id,
		last_event_time
	FROM analytics.current_batch_state
	WHERE warehouse_id = %(warehouse_id)s
	ORDER BY last_event_time DESC;
	"""

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query, {"warehouse_id": warehouse_id})
			return cur.fetchall()
