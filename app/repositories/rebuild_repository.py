from app.services.db.connection import get_analytics_connection
from psycopg import Connection


def truncate_snapshot(conn: Connection | None = None):
	query = "TRUNCATE TABLE analytics.current_batch_state;"

	if conn is not None:
		with conn.cursor() as cur:
			cur.execute(query)
		return

	with get_analytics_connection() as owned_conn:
		with owned_conn.cursor() as cur:
			cur.execute(query)


def rebuild_snapshot_data(conn: Connection | None = None) -> int:
	query = """
	WITH latest_events AS (
		SELECT DISTINCT ON (e.batch_id)
			e.batch_id,
			e.order_id,
			e.sku_id,
			e.warehouse_id,
			e.status_id,
			e.quantity,
			e.source_location_id,
			e.destination_location_id,
			e.event_time,
			e.status_reason_id,
			e.event_id
		FROM analytics.inventory_status_events e
		ORDER BY e.batch_id, e.event_time DESC, e.event_id DESC
	),
	filtered AS (
		SELECT
			le.batch_id,
			le.order_id,
			le.sku_id,
			le.warehouse_id,
			le.status_id,
			le.quantity,
			le.source_location_id,
			le.destination_location_id,
			le.event_time
		FROM latest_events le
		JOIN analytics.status_reason sr
			ON sr.status_reason_id = le.status_reason_id
		WHERE sr.is_tracking_finished = false
	)
	INSERT INTO analytics.current_batch_state (
		batch_id,
		order_id,
		sku_id,
		warehouse_id,
		status_id,
		quantity,
		source_location_id,
		destination_location_id,
		last_event_time
	)
	SELECT
		f.batch_id,
		f.order_id,
		f.sku_id,
		f.warehouse_id,
		f.status_id,
		f.quantity,
		f.source_location_id,
		f.destination_location_id,
		f.event_time
	FROM filtered f;
	"""

	if conn is not None:
		with conn.cursor() as cur:
			cur.execute(query)
			inserted_rows = cur.rowcount if cur.rowcount is not None else 0
		return int(inserted_rows)

	with get_analytics_connection() as owned_conn:
		with owned_conn.cursor() as cur:
			cur.execute(query)
			inserted_rows = cur.rowcount if cur.rowcount is not None else 0

	return int(inserted_rows)


def create_snapshot_backup():
	query = """
	CREATE TEMP TABLE snapshot_before AS
	SELECT
		batch_id,
		order_id,
		sku_id,
		warehouse_id,
		status_id,
		quantity,
		source_location_id,
		destination_location_id,
		last_event_time
	FROM analytics.current_batch_state;
	"""

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query)


def count_diff_before_after():
	query1 = """
	SELECT COUNT(*) AS cnt
	FROM (
		SELECT
			batch_id,
			order_id,
			sku_id,
			warehouse_id,
			status_id,
			quantity,
			source_location_id,
			destination_location_id,
			last_event_time
		FROM snapshot_before
		EXCEPT
		SELECT
			batch_id,
			order_id,
			sku_id,
			warehouse_id,
			status_id,
			quantity,
			source_location_id,
			destination_location_id,
			last_event_time
		FROM analytics.current_batch_state
	) AS diff;
	"""

	query2 = """
	SELECT COUNT(*) AS cnt
	FROM (
		SELECT
			batch_id,
			order_id,
			sku_id,
			warehouse_id,
			status_id,
			quantity,
			source_location_id,
			destination_location_id,
			last_event_time
		FROM analytics.current_batch_state
		EXCEPT
		SELECT
			batch_id,
			order_id,
			sku_id,
			warehouse_id,
			status_id,
			quantity,
			source_location_id,
			destination_location_id,
			last_event_time
		FROM snapshot_before
	) AS diff;
	"""

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query1)
			diff1 = cur.fetchone()

			cur.execute(query2)
			diff2 = cur.fetchone()

	return diff1, diff2
