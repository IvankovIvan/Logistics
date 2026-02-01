# app/services/data_sources/ingest_memory.py
from typing import List, Dict

from app.services.data_sources.base import CurrentStateDataSource
from app.services.ingest.rules import _warehouses_state, _shipments_state


class InMemoryIngestDataSource(CurrentStateDataSource):
    """
    Источник данных, читающий current-state,
    накопленный ingest'ом в памяти.

    Используется:
    - для локальной отладки ingest
    - для проверки логики без БД

    ⚠️ Не предназначен для production.
    """

    def get_warehouses(self) -> List[Dict]:
        return [
            {
                "id": payload.id,
                "name": payload.name,
                "lat": payload.lat,
                "lon": payload.lon,
                "status": payload.status,
            }
            for payload in (
                state["payload"] for state in _warehouses_state.values()
            )
        ]

    def get_shipments(self) -> List[Dict]:
        return [
            {
                "id": payload.id,
                "from_node": payload.from_warehouse_id,
                "to_node": payload.to_warehouse_id,
                "status": payload.status,
            }
            for payload in (
                state["payload"] for state in _shipments_state.values()
            )
        ]