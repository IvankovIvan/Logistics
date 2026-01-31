# app/services/data_sources/fake.py
from typing import List, Dict
from datetime import datetime

from services.data_sources.base import CurrentStateDataSource
from routers.warehouses import FAKE_WAREHOUSES
from routers.shipments import FAKE_SHIPMENTS


class FakeDataSource(CurrentStateDataSource):
    """
    FAKE-реализация источника данных.

    Используется:
    - для локальной разработки
    - как эталон поведения карты
    - как fallback до подключения БД

    Поведение должно 1-в-1 совпадать с предыдущей логикой.
    """

    def get_warehouses(self) -> List[Dict]:
        # FAKE_WAREHOUSES уже в нужной форме
        return FAKE_WAREHOUSES

    def get_shipments(self) -> List[Dict]:
        # FAKE_SHIPMENTS → приводим к простому dict-формату
        return [
            {
                "id": s.id,
                "from_warehouse_id": s.from_node,
                "to_warehouse_id": s.from_node,
                "status": s.status,
            }
            for s in FAKE_SHIPMENTS
        ]

    def get_last_updated(self) -> datetime:
        # FAKE-источник всегда "обновлён сейчас"
        return datetime.utcnow()