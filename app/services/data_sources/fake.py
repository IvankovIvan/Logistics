# app/services/data_sources/fake.py
from datetime import datetime
from typing import List, Dict

from app.services.data_sources.base import CurrentStateDataSource
from app.services.data_sources.fake_data import (
    FAKE_WAREHOUSES,
    FAKE_SHIPMENTS,
)


class FakeDataSource(CurrentStateDataSource):
    """
    FAKE-реализация источника current-state данных.
    Единственный источник — fake_data.py
    """

    def get_warehouses(self) -> List[Dict]:
        if any(w.get("quantity") is None for w in FAKE_WAREHOUSES):
            raise ValueError("warehouse missing quantity in fake data source")
        return FAKE_WAREHOUSES

    def get_shipments(self) -> List[Dict]:
        return FAKE_SHIPMENTS

    def get_last_updated(self) -> datetime:
        return datetime.utcnow()
