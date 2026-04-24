# /opt/Logistics/docs/_work/project-4-mssql-ingestion.md

# 📘 Project №4 --- MS SQL → Postgres Ingestion Pipeline (V2)

------------------------------------------------------------------------

## 1. Общая идея

Project №4 реализует надёжную доставку данных из внешней системы (MS
SQL) в аналитический слой (Postgres), используемый в Project №2.

Система построена по принципу:

source → extract → ingest → buffer → process

------------------------------------------------------------------------

## 2. Архитектурный поток

MS SQL (source_table) ↓ mssql-extractor ↓ POST
/api/analytics/ingest/events ↓ Postgres: - inventory_status_events
(buffer) ↓ analytics_worker ↓ current_batch_state (snapshot)

------------------------------------------------------------------------

## 3. Основные компоненты

### 3.1 MS SQL (Source)

-   хранит подготовленные события
-   содержит event_id (IDENTITY)
-   является временным буфером
-   очищается автоматически (retention policy ≥ 24 часа)
-   содержит индекс по (event_id)

------------------------------------------------------------------------

### 3.2 MS SQL Extractor

Сервис:

mssql-extractor

Функции:

-   читает данные из MS SQL через хранимую процедуру
-   использует ingest_cursor (из Postgres)
-   работает в адаптивном цикле (без scheduler)
-   отправляет batch в ingest API
-   выполняет retry
-   изолирует ошибки (split & DLQ)
-   НЕ взаимодействует напрямую с Postgres (кроме cursor)

Особенности:

-   подключение через pyodbc с pooling
-   connection timeout: 5--10 сек
-   query timeout: 30 сек

------------------------------------------------------------------------

### 🔧 3.2.2 Реализация extractor (добавлено)

Текущая реализация разбита на модули:

app/workers/mssql_extractor/ main.py ← orchestration mssql.py ← MS SQL
(fetch) postgres.py ← cursor

------------------------------------------------------------------------

### 3.2.1 MS SQL Stored Procedure

Процедура:

sp_get_events_after_id

Назначение:

-   возвращает batch событий после cursor
-   инкапсулирует SQL-логику

Сигнатура:

CREATE PROCEDURE sp_get_events_after_id @last_event_id BIGINT,
@batch_size INT AS BEGIN SET NOCOUNT ON;

    SELECT TOP (@batch_size)
        event_id,
        operation_id,
        batch_id,
        order_id,
        sku_id,
        warehouse_id,
        source_location_id,
        destination_location_id,
        status_id,
        status_reason_id,
        quantity,
        event_time,
        source_system
    FROM source_table
    WHERE event_id > @last_event_id
    ORDER BY event_id ASC;

END;

Вызов:

EXEC sp_get_events_after_id ?, ?

------------------------------------------------------------------------

### 3.3 Ingest API

Endpoint:

POST /api/analytics/ingest/events

Функции:

-   принимает batch событий (JSON)
-   вставляет в Postgres
-   гарантирует idempotency (operation_id + event_time)
-   возвращает per-event статус:
    -   applied
    -   duplicate
    -   rejected

------------------------------------------------------------------------

### 3.4 Event Store

Таблица:

analytics.inventory_status_events

-   append-only
-   partitioned
-   источник истины
-   хранит события как очередь (buffer)

------------------------------------------------------------------------

### 3.5 Analytics Worker

Функции:

-   читает события по event_id
-   использует processing_cursor
-   обновляет snapshot
-   обновляет cursor только после успешного batch

------------------------------------------------------------------------

### 3.6 Dead Letter Queue (DLQ)

Таблица:

analytics.ingest_dead_letter

Назначение:

-   хранит "битые" события
-   содержит payload, error, created_at, source_event_id
-   используется для анализа и replay

------------------------------------------------------------------------

## 4. Cursor модель

ingest_cursor --- что загружено в Postgres\
processing_cursor --- что обработано worker'ом

Хранение:

analytics.worker_state

------------------------------------------------------------------------

### 🔧 Реализация cursor (добавлено)

-   реализован в postgres.py\
-   используется psycopg + dict_row\
-   используется cast для корректной типизации

------------------------------------------------------------------------

## 5. Ingestion логика

EXEC sp_get_events_after_id ingest_cursor, batch_size

После успешной вставки:

ingest_cursor = max(event_id batch)

Правила:

-   cursor обновляется только после успеха
-   порядок строго по event_id

------------------------------------------------------------------------

### 🔧 Важное изменение (добавлено)

READPAST НЕ используется\
Причина: риск потери данных

------------------------------------------------------------------------

## 6. Processing логика

SELECT WHERE event_id \> processing_cursor ORDER BY event_id LIMIT
batch_size

------------------------------------------------------------------------

## 7. Буферизация

Postgres = очередь\
ingestion и processing независимы

------------------------------------------------------------------------

## 8. Cleanup

retention ≥ 24 часа\
должен покрывать worst-case lag

------------------------------------------------------------------------

## 9. Гарантии

-   нет потерь\
-   нет дублей\
-   порядок сохраняется

------------------------------------------------------------------------

## 10. Инварианты

-   cursor монотонный\
-   события не теряются\
-   ingestion независим

------------------------------------------------------------------------

## 11. Ограничения

-   один extractor\
-   batch processing

------------------------------------------------------------------------

## 12. Итог

Надёжный ingestion pipeline

------------------------------------------------------------------------

## 13. Статус (обновлён)

  Компонент          Статус
  ------------------ --------
  MSSQL connection   ✔
  Postgres cursor    ✔
  Batch fetch        ✔
  Ingest API         ⏳
  Cursor update      ⏳
  Retry / DLQ        ⏳

------------------------------------------------------------------------

## 14. Текущий этап

fetch → готово\
cursor → готово\
API → следующий шаг

------------------------------------------------------------------------

Архитектура НЕ переписана, а расширена.
