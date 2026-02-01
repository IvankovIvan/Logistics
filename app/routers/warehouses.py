# app/routers/warehouses.py
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models import Warehouse, WarehouseStatus
# Временное хранилище "как будто БД".
from app.services.data_sources.fake_data import FAKE_WAREHOUSES

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

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