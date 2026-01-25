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

    # --- новые отправки для "живой" карты ---

    Shipment(
        id="shp-1003",
        **{"from": "hel-01", "to": "spb-01"},
        status=ShipmentStatus.in_transit,
        updated_at=datetime(2026, 1, 18, 10, 15, tzinfo=timezone.utc),
    ),
    Shipment(
        id="shp-1004",
        **{"from": "msk-01", "to": "kzn-01"},
        status=ShipmentStatus.planned,
        updated_at=datetime(2026, 1, 18, 11, 40, tzinfo=timezone.utc),
    ),
    Shipment(
        id="shp-1005",
        **{"from": "kzn-01", "to": "ekb-01"},
        status=ShipmentStatus.in_transit,
        updated_at=datetime(2026, 1, 18, 12, 5, tzinfo=timezone.utc),
    ),
    Shipment(
        id="shp-1006",
        **{"from": "ekb-01", "to": "nsk-01"},
        status=ShipmentStatus.planned,
        updated_at=datetime(2026, 1, 18, 12, 30, tzinfo=timezone.utc),
    ),
    Shipment(
        id="shp-1007",
        **{"from": "mur-01", "to": "msk-01"},
        status=ShipmentStatus.delivered,
        updated_at=datetime(2026, 1, 17, 6, 0, tzinfo=timezone.utc),
    ),
    Shipment(
        id="shp-1008",
        **{"from": "sochi-01", "to": "msk-01"},
        status=ShipmentStatus.cancelled,
        updated_at=datetime(2026, 1, 16, 20, 0, tzinfo=timezone.utc),
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
    "/now",
    summary="Витрина перевозок на сейчас",
    description="Возвращает агрегированное текущее состояние: сколько перевозок в каждом статусе.",
)
def shipments_now():
    counts = {s.value: 0 for s in ShipmentStatus}
    for sh in FAKE_SHIPMENTS:
        counts[sh.status.value] += 1

    return {
        "total": len(FAKE_SHIPMENTS),
        "by_status": counts,
    }

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

