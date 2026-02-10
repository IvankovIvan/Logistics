# app/services/data_sources/postgres/datasource.py
from datetime import datetime

from app.services.data_sources.base import CurrentStateDataSource
from app.services.data_sources.postgres.connection import get_connection
from app.services.data_sources.postgres import queries


class PostgresDataSource(CurrentStateDataSource):
    """
    Read-side источник данных из PostgreSQL (current-state).

    Гарантии:
    - читает ТОЛЬКО текущие таблицы
    - не знает про ingest и события
    - формат данных совместим с map_builder
    """

    def get_warehouses(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queries.WAREHOUSES_CURRENT)
                warehouses = cur.fetchall()
                if any(w.get("quantity") is None for w in warehouses):
                    raise ValueError("warehouse missing quantity in postgres data source")
                return warehouses

    def get_shipments(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queries.SHIPMENTS_CURRENT)
                return cur.fetchall()

    def get_last_updated(self) -> datetime:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queries.LAST_UPDATED)

                row = cur.fetchone()

                # Защитный инвариант: запрос ВСЕГДА возвращает строку
                if row is None:
                    raise RuntimeError(
                        "LAST_UPDATED query returned no rows (unexpected)"
                    )

                # LAST_UPDATED всегда возвращает 1 колонку
                return row[0]
