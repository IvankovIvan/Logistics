from app.models.analytics_map_response import (
    MapWarehouse,
    WarehouseMetrics,
    StatusQuantity,
)
from app.services.analytics.map.service import AnalyticsMapWarehouse


def to_map_warehouse(item: AnalyticsMapWarehouse) -> MapWarehouse:
    metrics = item["metrics"]

    return MapWarehouse(
        warehouse_id=item["warehouse_id"],
        name=item["name"],
        lat=item["lat"],
        lon=item["lon"],
        metrics=WarehouseMetrics(
            total=metrics["total"],
            by_status=[
                StatusQuantity(
                    status_id=s["status_id"],
                    quantity=s["quantity"],
                )
                for s in metrics["by_status"]
            ],
        ),
    )
