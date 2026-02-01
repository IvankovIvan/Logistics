# app/services/ingest/rules.py
from datetime import datetime
from typing import Dict, Any

from models.ingest import (
    IngestEvent,
    WarehouseIngestEvent,
    ShipmentIngestEvent,
)

# =====================================================
# In-memory current-state (TEMPORARY)
# =====================================================
# ⚠️ ВАЖНО:
# - используется только до подключения БД
# - при рестарте приложения очищается
# - полностью повторяет будущую семантику current-state таблиц
# =====================================================

_warehouses_state: Dict[str, Dict[str, Any]] = {}
_shipments_state: Dict[str, Dict[str, Any]] = {}


def _is_stale(event_time: datetime, last_event_time: datetime) -> bool:
    """
    Проверяет, является ли событие устаревшим.

    Устаревшее = событие с event_time < последнего применённого.
    """
    return event_time < last_event_time


def apply_event(event: IngestEvent) -> None:
    """
    Применяет одно ingest-событие к in-memory current-state.

    Может выбросить ValueError:
    - если событие логически некорректно
    """

    # =================================================
    # Warehouse events
    # =================================================
    if isinstance(event, WarehouseIngestEvent):
        payload = event.payload
        current = _warehouses_state.get(payload.id)

        # --- stale check ---
        if current and _is_stale(event.event_time, current["last_event_time"]):
            raise ValueError("stale warehouse event")

        # --- upsert ---
        _warehouses_state[payload.id] = {
            "payload": payload,
            "last_event_time": event.event_time,
        }
        return

    # =================================================
    # Shipment events
    # =================================================
    if isinstance(event, ShipmentIngestEvent):
        payload = event.payload

        # --- reference integrity ---
        if payload.from_warehouse_id not in _warehouses_state:
            raise ValueError(f"unknown from_warehouse_id: {payload.from_warehouse_id}")

        if payload.to_warehouse_id not in _warehouses_state:
            raise ValueError(f"unknown to_warehouse_id: {payload.to_warehouse_id}")

        current = _shipments_state.get(payload.id)

        # --- stale check ---
        if current and _is_stale(event.event_time, current["last_event_time"]):
            raise ValueError("stale shipment event")

        # --- upsert ---
        _shipments_state[payload.id] = {
            "payload": payload,
            "last_event_time": event.event_time,
        }
        return

    # =================================================
    # Safety net (should never happen due to discriminator)
    # =================================================
    raise ValueError("unsupported ingest event type")