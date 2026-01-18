from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models import Shipment, ShipmentStatus

router = APIRouter(prefix="/shipments", tags=["shipments"])

FAKE_SHIPMENTS: List[Shipment] = [
    Shipment(
        id="shp-1001",
        **{"from": "spb-01", "to": "msk-01"},
        status=ShipmentStatus.in_transit,
        updated_at=datetime(2026, 1, 17, 14, 32, tzinfo=timezone.utc),
    ),
    Shipment(
        id="shp-1002",
        **{"from": "msk-01", "to": "spb-01"},
        status=ShipmentStatus.planned,
        updated_at=datetime(2026, 1, 17, 9, 5, tzinfo=timezone.utc),
    ),
]


@router.get(
    "",
    response_model=List[Shipment],
    summary="Список перевозок",
    description="Возвращает список перевозок в текущем состоянии (без истории).",
)
def get_shipments(
    status: Optional[ShipmentStatus] = Query(
        None,
        description="Фильтр по статусу перевозки: planned, in_transit, delivered, cancelled",
    ),
):
    res = FAKE_SHIPMENTS
    if status is not None:
        res = [s for s in res if s.status == status]
    return res


@router.get(
    "/{shipment_id}",
    response_model=Shipment,
    summary="Получить перевозку по id",
    description="Возвращает текущее состояние конкретной перевозки.",
)
def get_shipment(shipment_id: str):
    for s in FAKE_SHIPMENTS:
        if s.id == shipment_id:
            return s
    raise HTTPException(status_code=404, detail="Shipment not found")
