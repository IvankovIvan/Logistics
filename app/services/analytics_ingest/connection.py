# app/services/analytics_ingest/connection.py
"""
PostgreSQL connection для analytics-db.

Этот модуль переэкспортирует get_analytics_connection из app.services.db.connection.
Оставлен для обратной совместимости.
"""

from app.services.db.connection import get_analytics_connection

__all__ = ["get_analytics_connection"]
