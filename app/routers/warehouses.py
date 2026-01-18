from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from models import Warehouse, WarehouseStatus

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

FAKE_WAREHOUSES: List[Warehouse] = [
    Warehouse(id="spb-01", name="Saint Petersburg DC", status=WarehouseStatus.active),
    Warehouse(id="msk-01", name="Moscow Hub", status=WarehouseStatus.active),
]


@router.get(
    "",
    response_model=List[Warehouse],
    summary="Список складов",
    description="Возвращает список всех складов. Поддерживает фильтрацию по статусу.",
)
def get_warehouses(
    status: Optional[WarehouseStatus] = Query(None, description="Фильтр по статусу склада"),
):
    res = FAKE_WAREHOUSES
    if status is not None:
        res = [w for w in res if w.status == status]
    return res


@router.get(
    "/{warehouse_id}",
    response_model=Warehouse,
    summary="Получить склад по id",
    description="Возвращает один склад по его идентификатору.",
)
def get_warehouse(warehouse_id: str):
    for w in FAKE_WAREHOUSES:
        if w.id == warehouse_id:
            return w
    raise HTTPException(status_code=404, detail="Warehouse not found")
