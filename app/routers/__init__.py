"""
Единая точка подключения всех роутеров приложения.

main.py должен импортировать роутеры ТОЛЬКО отсюда.
"""

from .warehouses import router as warehouses_router
from .shipments import router as shipments_router
from .analytics_ingest import router as analytics_ingest_router
from .analytics_map import router as analytics_map_router

__all__ = [
    "warehouses_router",
    "shipments_router",
    "ingest_router",
    "analytics_ingest_router",
    "analytics_map_router",
]