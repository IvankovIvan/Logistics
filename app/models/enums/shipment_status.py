from enum import Enum


class ShipmentStatus(str, Enum):
    """
    Статус перевозки.

    planned      — перевозка создана, но ещё не начата
    in_transit   — груз в пути
    delivered    — груз доставлен
    cancelled    — перевозка отменена
    """
    planned = "planned"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"
