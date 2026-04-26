"""Response models for analytics map API."""

from pydantic import BaseModel


class StatusQuantity(BaseModel):
    """Одна строка метрики по статусу склада."""

    status_id: int
    quantity: int


class WarehouseMetrics(BaseModel):
    """Агрегированные метрики склада."""

    total: int
    by_status: list[StatusQuantity]


class MapWarehouse(BaseModel):
    """Формат одного склада для analytics map API."""

    warehouse_id: int
    name: str
    lat: float
    lon: float
    metrics: WarehouseMetrics


class AnalyticsMapResponse(BaseModel):
    """Response для GET /api/analytics/map."""

    warehouses: list[MapWarehouse]
    routes: list = []
