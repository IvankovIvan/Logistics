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

------------------------------------------------------------------------

### 3.2 MS SQL Extractor

Сервис:

mssql-extractor

Функции:

-   читает данные из MS SQL
-   использует ingest_cursor (из Postgres)
-   работает в адаптивном цикле (без scheduler)
-   отправляет batch в ingest API
-   выполняет retry
-   изолирует ошибки (split & DLQ)
-   НЕ взаимодействует напрямую с Postgres (кроме cursor)

------------------------------------------------------------------------

### 3.3 Ingest API

Endpoint:

POST /api/analytics/ingest/events

Функции:

-   принимает batch событий (JSON)
-   вставляет в Postgres
-   гарантирует idempotency (operation_id + event_time)
-   возвращает per-event статус (applied / duplicate / rejected)

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
-   содержит payload, ошибку и timestamp
-   используется для анализа и возможного replay

------------------------------------------------------------------------

## 4. Cursor модель

Система использует ДВА cursor'а:

ingest_cursor --- что загружено в Postgres\
processing_cursor --- что обработано worker'ом

Хранение:

analytics.worker_state:

-   mssql_extractor → ingest_cursor\
-   analytics_worker → processing_cursor

------------------------------------------------------------------------

## 5. Ingestion логика

Extractor выполняет:

SELECT WHERE event_id \> ingest_cursor ORDER BY event_id LIMIT
batch_size

После успешной вставки:

ingest_cursor = max(event_id batch)

Правила:

-   cursor обновляется ТОЛЬКО после полного успеха batch
-   rejected события изолируются (не блокируют pipeline)

------------------------------------------------------------------------

## 6. Processing логика

Worker выполняет:

SELECT WHERE event_id \> processing_cursor ORDER BY event_id LIMIT
batch_size

После обработки:

processing_cursor обновляется

------------------------------------------------------------------------

## 7. Буферизация

Postgres выступает как очередь:

-   ingestion быстрый (максимально возможный)
-   processing независимый (может отставать)

------------------------------------------------------------------------

## 8. Cleanup

Очистка выполняется MS SQL автоматически:

-   retention policy ≥ 24 часа
-   данные удаляются по времени, не по cursor

⚠️ Требование:

retention должен покрывать worst-case lag системы

------------------------------------------------------------------------

## 9. Гарантии

-   нет потерь данных (cursor обновляется после commit)
-   нет дублей (idempotency)
-   порядок событий сохраняется (event_id)
-   система устойчива к сбоям (retry + DLQ)

------------------------------------------------------------------------

## 10. Инварианты

1.  extractor использует ingest_cursor\
2.  worker использует processing_cursor\
3.  ingestion и processing независимы\
4.  Postgres = буфер (очередь)\
5.  MS SQL = источник + временный буфер\
6.  cursor монотонный\
7.  cursor обновляется только после успеха\
8.  rejected события НЕ блокируют pipeline

------------------------------------------------------------------------

## 11. Ограничения

-   один extractor\
-   один worker\
-   batch processing\
-   JSON транспорт\
-   cleanup не привязан к cursor

------------------------------------------------------------------------

## 12. Итог

Система реализует:

-   надёжный ingestion pipeline\
-   разделение ingestion и processing\
-   устойчивую архитектуру\
-   масштабируемую модель\
-   обработку ошибок через DLQ

------------------------------------------------------------------------

## 13. Статус

  Компонент      Статус
  -------------- --------
  Extractor      ✔
  Ingest API     ✔
  Event Store    ✔
  Worker         ✔
  Cursor model   ✔
  Cleanup        ✔
  DLQ            ✔

------------------------------------------------------------------------

**Архитектура Project №4 (V2) завершена.**
