from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models import Warehouse, WarehouseStatus

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

# Временное хранилище "как будто БД".
# Важно: это list[dict], поэтому ниже в коде используем доступ w["id"], w["status"].
FAKE_WAREHOUSES = [
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