from enum import Enum


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
