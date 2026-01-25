from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from types import SimpleNamespace
from typing import Type, TypeVar

from domain.protocols import ShipmentLike, WarehouseLike

TEnum = TypeVar("TEnum", bound=Enum)


def coerce_enum(value: object, enum_cls: Type[TEnum], default: TEnum) -> TEnum:
    """
    Приводит строку/enum к нужному enum и не падает на мусоре.
    Здесь правим логику, если источник статусов поменяется.
    """

    if isinstance(value, enum_cls):
        return value
    if value is None:
        return default
    try:
        return enum_cls(str(value))
    except Exception:
        return default


def normalize_warehouse(item: WarehouseLike | Mapping[str, object]) -> WarehouseLike:
    """
    Приводит dict к объекту с атрибутами, чтобы код карты был одинаковым.
    Здесь правим, когда FAKE_* заменим на БД/ингест.
    """

    if isinstance(item, Mapping):
        return SimpleNamespace(**item)  # type: ignore[return-value]
    return item


def normalize_shipment(item: ShipmentLike | Mapping[str, object]) -> ShipmentLike:
    """
    Приводит dict к объекту с атрибутами, чтобы код карты был одинаковым.
    Здесь правим, когда FAKE_* заменим на БД/ингест.
    """

    if isinstance(item, Mapping):
        return SimpleNamespace(**item)  # type: ignore[return-value]
    return item
