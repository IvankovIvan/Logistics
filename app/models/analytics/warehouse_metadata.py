from pydantic import BaseModel


class AnalyticsWarehouseStatus(BaseModel):
    status_id: int
    status_text: str
    count: int
    sum: int


class AnalyticsWarehouseMetrics(BaseModel):
    count: int
    sum: int
    by_status: list[AnalyticsWarehouseStatus]


class AnalyticsWarehouseMetadata(BaseModel):
    warehouse_id: int
    name: str
    city: str
    warehouse_type: str
    metrics: AnalyticsWarehouseMetrics
