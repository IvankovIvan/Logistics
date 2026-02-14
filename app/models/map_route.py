from typing import List, Tuple

from pydantic import BaseModel, Field

from .enums import ShipmentStatus


class MapRoute(BaseModel):
    """
    Маршрут для карты.

    coordinates — готовая линия (LineString-подобный массив точек),
    чтобы фронт просто рисовал и не склеивал from/to.
    """
    id: str = Field(..., description="ID перевозки")
    status: ShipmentStatus = Field(..., description="Статус перевозки")
    # Project 1.6.a: required shipment volume (current-state).
    volume: int = Field(
        ...,
        description="Абсолютный объём перевозки (>= 0, current-state)",
    )

    from_id: str = Field(..., alias="from", description="ID склада отправления", examples=["spb-01"])
    to_id: str = Field(..., alias="to", description="ID склада назначения", examples=["msk-01"])

    coordinates: List[Tuple[float, float]] = Field(
        ...,
        description="Координаты линии маршрута: [(lon, lat), (lon, lat)]",
        examples=[[(30.3141, 59.9386), (37.6173, 55.7558)]],
    )

    model_config = {"populate_by_name": True}
