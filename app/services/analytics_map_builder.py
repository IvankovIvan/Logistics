"""
Analytics map builder for Project #3.

Назначение:
- собрать карту из analytics-слоя (без OLTP)
- использовать master-справочник складов analytics.warehouses
- использовать агрегаты из analytics.current_batch_state
- вернуть структуру, удобную для API-слоя карты

Инварианты:
- НЕ трогает существующий app/services/map_builder.py
- НЕ использует JSON в SQL
- НЕ использует status_reason_id
- НЕ фильтрует склады: каждый warehouse из справочника попадает в ответ
"""

from __future__ import annotations

from app.services.analytics.map.service import build_analytics_map_warehouses

__all__ = ["build_analytics_map_warehouses"]
