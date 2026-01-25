from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models import Warehouse, WarehouseStatus

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

# Временное хранилище "как будто БД".
# Важно: это list[dict], поэтому ниже в коде используем доступ w["id"], w["status"].
FAKE_WAREHOUSES = [
    # База
    {
        "id": "spb-01",
        "name": "Saint Petersburg DC",
        "status": "active",
        "lat": 59.9311,
        "lon": 30.3609,
    },
    {
        "id": "msk-01",
        "name": "Moscow Hub",
        "status": "active",
        "lat": 55.7558,
        "lon": 37.6173,
    },

    # Новые города — чтобы на карте было больше точек
    {
        "id": "hel-01",
        "name": "Helsinki Crossdock",
        "status": "active",
        "lat": 60.1699,
        "lon": 24.9384,
    },
    {
        "id": "kzn-01",
        "name": "Kazan Sort Center",
        "status": "active",
        "lat": 55.7903,
        "lon": 49.1347,
    },
    {
        "id": "ekb-01",
        "name": "Yekaterinburg Hub",
        "status": "maintenance",
        "lat": 56.8389,
        "lon": 60.6057,
    },
    {
        "id": "nsk-01",
        "name": "Novosibirsk DC",
        "status": "active",
        "lat": 55.0084,
        "lon": 82.9357,
    },
    {
        "id": "mur-01",
        "name": "Murmansk Arctic Depot",
        "status": "active",
        "lat": 68.9585,
        "lon": 33.0827,
    },
    {
        "id": "sochi-01",
        "name": "Sochi Resort Hub",
        "status": "closed",
        "lat": 43.5855,
        "lon": 39.7231,
    },
]


@router.get(
    "",
    response_model=List[Warehouse],
    summary="Список складов",
    description="Возвращает список всех складов. Поддерживает фильтрацию по статусу.",
)
def get_warehouses(
    status: Optional[WarehouseStatus] = Query(
        None, description="Фильтр по статусу склада"
    ),
):
    # res — list[dict], FastAPI сам приведет dict -> Warehouse по response_model
    res = FAKE_WAREHOUSES
    if status is not None:
        # status приходит как enum WarehouseStatus, а в FAKE_WAREHOUSES хранится строка.
        # Поэтому сравниваем со status.value.
        res = [w for w in res if w["status"] == status.value]
    return res


@router.get(
    "/{warehouse_id}",
    response_model=Warehouse,
    summary="Получить склад по id",
    description="Возвращает один склад по его идентификатору.",
)
def get_warehouse(warehouse_id: str):
    for w in FAKE_WAREHOUSES:
        if w["id"] == warehouse_id:
            return w
    raise HTTPException(status_code=404, detail="Warehouse not found")