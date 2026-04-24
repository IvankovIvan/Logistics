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

import pyodbc


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
) -> list[dict[str, object]]:
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
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        cursor.close()
