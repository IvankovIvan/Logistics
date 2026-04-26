from app.services.db.connection import get_analytics_connection


def create_partition(event_time, cur=None):
	query = """
	SELECT analytics.create_month_partition(%(event_time)s) AS created_partition;
	"""

	if cur is not None:
		cur.execute(query, {"event_time": event_time})
		return cur.fetchone()

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query, {"event_time": event_time})
			return cur.fetchone()


def insert_event(params, cur=None):
	query = """
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
		%(planned_departure_time)s,
		%(source_system)s,
		%(operation_id)s
	)
	ON CONFLICT (operation_id, event_time) DO NOTHING
	RETURNING operation_id;
	"""

	if cur is not None:
		cur.execute(query, params)
		return cur.fetchone()

	with get_analytics_connection() as conn:
		with conn.cursor() as cur:
			cur.execute(query, params)
			return cur.fetchone()
