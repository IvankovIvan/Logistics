# app/services/data_sources/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional


class CurrentStateDataSource(ABC):
    """
    Абстрактный источник current-state данных для карты.

    Назначение:
    - отдать снапшот текущего состояния логистики
    - не знать про ingest, БД, события и историю
    - использоваться map_builder'ом как read-model

    Любая реализация (FAKE / DB / CACHE) ОБЯЗАНА
    возвращать данные в этой форме.
    """

    @abstractmethod
    def get_warehouses(self) -> List[Dict]:
        """
        Возвращает список складов в текущем состоянии.

        Каждый элемент:
        {
            id: str,
            name: str,
            lat: float,
            lon: float,
            status: str
        }
        """
        raise NotImplementedError

    @abstractmethod
    def get_shipments(self) -> List[Dict]:
        """
        Возвращает список перевозок (маршрутов) в текущем состоянии.

        Каждый элемент:
        {
            id: str,
            from_warehouse_id: str,
            to_warehouse_id: str,
            status: str
        }
        """
        raise NotImplementedError

    def get_last_updated(self) -> Optional[datetime]:
        """
        Необязательная метка последнего обновления current-state.

        Используется фронтом как lastUpdated.
        По умолчанию отсутствует.
        """
        return None