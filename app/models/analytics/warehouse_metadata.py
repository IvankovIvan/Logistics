from pydantic import BaseModel


class AnalyticsWarehouseMetadata(BaseModel):
    warehouse_id: int
    name: str
    city: str
    warehouse_type: str
