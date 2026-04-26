# app/workers/mssql_extractor/mssql.py
"""
Утилиты подключения и чтения событий из MS SQL.

Здесь сосредоточено всё, что касается MS SQL:
- чтение переменных окружения для подключения;
- формирование ODBC connection string;
- открытие соединения;
- вызов хранимой процедуры и возврат событий в виде словарей.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TypedDict

import pyodbc


class EventRow(TypedDict):
    event_id: int
    operation_id: int
    batch_id: int
    order_id: int
    sku_id: int
    warehouse_id: int
    source_location_id: int | None
    destination_location_id: int | None
    status_id: int
    status_reason_id: int
    quantity: int
    event_time: str
    planned_departure_time: str | None
    source_system: int


# Включаем pooling на уровне драйвера pyodbc,
# чтобы повторные подключения переиспользовали ресурсы соединений.
pyodbc.pooling = True


def _get_required_env(name: str) -> str:
    """
    Читает обязательную переменную окружения.

    Зачем это нужно:
    - параметры подключения не должны быть захардкожены в коде;
    - конфигурация задается через env для разных сред (dev/stage/prod).
    """
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Не задана обязательная переменная окружения: {name}")
    return value


def _build_connection_string() -> str:
    """
    Формирует ODBC-строку подключения к MS SQL.

    Параметры берутся из env:
    - MSSQL_HOST, MSSQL_PORT, MSSQL_DB, MSSQL_USER, MSSQL_PASSWORD, MSSQL_DRIVER

    Таймаут подключения задается 8 секунд (в диапазоне 5-10 сек по требованию).
    """
    driver = _get_required_env("MSSQL_DRIVER")
    host = _get_required_env("MSSQL_HOST")
    port = _get_required_env("MSSQL_PORT")
    database = _get_required_env("MSSQL_DB")
    user = _get_required_env("MSSQL_USER")
    password = _get_required_env("MSSQL_PASSWORD")

    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=yes;TrustServerCertificate=yes;"
        "Connection Timeout=8;"
    )


def get_connection() -> pyodbc.Connection:
    """
    Возвращает открытое подключение к MS SQL.

    autocommit=False: транзакционное поведение по умолчанию.
    """
    return pyodbc.connect(_build_connection_string(), autocommit=False)


def fetch_batch(
    conn: pyodbc.Connection,
    ingest_cursor: int,
    batch_size: int,
) -> list[EventRow]:
    """
    Читает порцию событий из MS SQL начиная с ingest_cursor.

    ingest_cursor — last_processed_event_id: воркер читает только те события,
    у которых event_id > ingest_cursor. Это гарантирует, что одно и то же
    событие не будет обработано дважды после перезапуска.

    ORDER BY event_id внутри процедуры критически важен: только при строгом
    порядке можно безопасно обновить watermark после batch-а, не пропустив
    промежуточных событий.

    Возвращает список словарей — по одному на каждую строку результата.
    """
    cursor = conn.cursor()
    try:
        # Таймаут выполнения SQL-запроса/процедуры: 30 секунд.
        # cursor.timeout = 30

        # Параметры передаются через ? — защита от SQL-инъекций.
        cursor.execute("EXEC sp_get_events_after_id ?, ?", ingest_cursor, batch_size)

        columns = [col[0] for col in cursor.description]

        result: list[EventRow] = []
        for row in cursor.fetchall():
            values_by_column = {name: value for name, value in zip(columns, row)}

            event_time_value = values_by_column["event_time"]
            if isinstance(event_time_value, datetime):
                event_time_str = event_time_value.isoformat()
            else:
                event_time_str = str(event_time_value)

            planned_departure_time_value = values_by_column.get("planned_departure_time")
            if planned_departure_time_value is None:
                planned_departure_time_str = None
            elif isinstance(planned_departure_time_value, datetime):
                planned_departure_time_str = planned_departure_time_value.isoformat()
            else:
                planned_departure_time_str = str(planned_departure_time_value)

            row_dict: EventRow = {
                "event_id": int(values_by_column["event_id"]),
                "operation_id": int(values_by_column["operation_id"]),
                "batch_id": int(values_by_column["batch_id"]),
                "order_id": int(values_by_column["order_id"]),
                "sku_id": int(values_by_column["sku_id"]),
                "warehouse_id": int(values_by_column["warehouse_id"]),
                "source_location_id": (
                    None
                    if values_by_column["source_location_id"] is None
                    else int(values_by_column["source_location_id"])
                ),
                "destination_location_id": (
                    None
                    if values_by_column["destination_location_id"] is None
                    else int(values_by_column["destination_location_id"])
                ),
                "status_id": int(values_by_column["status_id"]),
                "status_reason_id": int(values_by_column["status_reason_id"]),
                "quantity": int(values_by_column["quantity"]),
                "event_time": event_time_str,
                "planned_departure_time": planned_departure_time_str,
                "source_system": int(values_by_column["source_system"]),
            }

            result.append(row_dict)

        return result
    finally:
        cursor.close()
