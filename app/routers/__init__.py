"""
Единая точка подключения всех роутеров приложения.

main.py должен импортировать роутеры ТОЛЬКО отсюда.
"""

from .analytics_ingest import router as analytics_ingest_router
from .analytics_map import router as analytics_map_router

__all__ = [
    "analytics_ingest_router",
    "analytics_map_router",
]