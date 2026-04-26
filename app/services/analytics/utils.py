"""Utilities for analytics service layer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _as_mapping(row: Any) -> Mapping[str, Any]:
    """
    Приводит строку курсора к Mapping.

    Ожидается dict_row от psycopg, но защитно проверяем тип,
    чтобы не возвращать молча некорректные данные.
    """

    if not isinstance(row, Mapping):
        raise TypeError("Expected mapping-like row from psycopg cursor")
    return row
