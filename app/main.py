"""
Logistics API

Минимальный API для логистической системы.
Пока работает без базы данных и возвращает захардкоженные данные.

Назначение:
- показать структуру API
- зафиксировать контракты
- подготовить основу для подключения БД и ingest
"""

from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# APPLICATION
# -------------------------------------------------------------------

app = FastAPI(
    title="Logistics API",
    description="API для управления складами и перевозками",
    version="0.1.0",
)


# -------------------------------------------------------------------
# ENUMS (справочники состояний)
# -------------------------------------------------------------------

class WarehouseStatus(str, Enum):
    """
    Статус склада.

    active       — склад работает
    closed       — склад закрыт
    maintenance  — склад временно недоступен (ремонт и т.п.)
    """
    active = "active"
    closed = "closed"
    maintenance = "maintenance"


class ShipmentStatus(str, Enum):
    """
    Статус перевозки.

    planned      — перевозка запланирована
    in_transit  — груз в пути
    delivered   — доставлено
    cancelled   — отменено
    """
    planned = "planned"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


# -------------------------------------------------------------------
# MODELS (контракты API)
# -------------------------------------------------------------------

class Warehouse(BaseModel):
    """
    Склад / логистический узел.

    Используется как точка отправки или назначения перевозок.
    """
    id: str = Field(..., description="Уникальный идентификатор склада")
    name: str = Field(..., description="Человекочитаемое название склада")
    status: WarehouseStatus = Field(..., description="Текущий статус склада")


class Shipment(BaseModel):
    """
    Перевозка груза между двумя складами.

    Возвращает ТОЛЬКО текущее состояние (без истории).
    """

    id: str = Field(..., description="Уникальный идентификатор перевозки")

    from_node: str = Field(
        ...,
        alias="from",
        description="Склад отправления (warehouse id)",
        examples=["spb-01"],
    )

    to_node: str = Field(
        ...,
        alias="to",
        description="Склад назначения (warehouse id)",
        examples=["msk-01"],
    )

    status: ShipmentStatus = Field(
        ...,
        description="Текущий статус перевозки",
    )

    updated_at: datetime = Field(
        ...,
        description="Дата и время последнего обновления состояния",
        examples=["2026-01-17T14:32:00Z"],
    )

    class Config:
        populate_by_name = True


# -------------------------------------------------------------------
# FAKE DATA (временная заглушка вместо БД)
# -------------------------------------------------------------------

FAKE_WAREHOUSES: List[Warehouse] = [
    Warehouse(id="spb-01", name="Saint Petersburg DC", status=WarehouseStatus.active),
    Warehouse(id="msk-01", name="Moscow Hub", status=WarehouseStatus.active),
]

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


# -------------------------------------------------------------------
# SERVICE
# -------------------------------------------------------------------

@app.get(
    "/",
    summary="Health-check",
    description="Проверка, что сервис запущен и отвечает",
    tags=["service"],
)
def health():
    return {"status": "ok"}


# -------------------------------------------------------------------
# WAREHOUSES
# -------------------------------------------------------------------

@app.get(
    "/warehouses",
    response_model=List[Warehouse],
    summary="Список складов",
    description="Возвращает список всех складов. Поддерживает фильтрацию по статусу.",
    tags=["warehouses"],
)
def get_warehouses(
    status: Optional[WarehouseStatus] = Query(
        None,
        description="Фильтр по статусу склада",
    ),
):
    """
    Получить список складов.
    """
    res = FAKE_WAREHOUSES
    if status is not None:
        res = [w for w in res if w.status == status]
    return res


@app.get(
    "/warehouses/{warehouse_id}",
    response_model=Warehouse,
    summary="Получить склад по id",
    description="Возвращает один склад по его идентификатору",
    tags=["warehouses"],
)
def get_warehouse(warehouse_id: str):
    """
    Получить информацию о конкретном складе.
    """
    for w in FAKE_WAREHOUSES:
        if w.id == warehouse_id:
            return w
    raise HTTPException(status_code=404, detail="Warehouse not found")


# -------------------------------------------------------------------
# SHIPMENTS
# -------------------------------------------------------------------

@app.get(
    "/shipments",
    response_model=List[Shipment],
    summary="Список перевозок",
    description="Возвращает список перевозок в текущем состоянии (без истории)",
    tags=["shipments"],
)
def get_shipments(
    status: Optional[ShipmentStatus] = Query(
        None,
        description="Фильтр по статусу перевозки",
    ),
):
    """
    Получить список перевозок.
    """
    res = FAKE_SHIPMENTS
    if status is not None:
        res = [s for s in res if s.status == status]
    return res


@app.get(
    "/shipments/{shipment_id}",
    response_model=Shipment,
    summary="Получить перевозку по id",
    description="Возвращает текущее состояние конкретной перевозки",
    tags=["shipments"],
)
def get_shipment(shipment_id: str):
    """
    Получить одну перевозку по идентификатору.
    """
    for s in FAKE_SHIPMENTS:
        if s.id == shipment_id:
            return s
    raise HTTPException(status_code=404, detail="Shipment not found")