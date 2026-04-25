# 📘 SYSTEM ARCHITECTURE — Logistics Platform (V1)

---

## 1. Общая идея

Система реализует полный цикл обработки логистических данных:

OLTP → Events → Snapshot → Analytics → UI

Назначение:

- хранить операционные данные
- обрабатывать события
- строить аналитическое состояние
- визуализировать данные
- предоставлять drill-down

---

## 2. Архитектурный поток

[Project 1] OLTP (current state)         ↓ [Project 4] MS SQL (source events)         ↓ mssql-extractor         ↓ POST /api/analytics/ingest/events         ↓ [Project 2] Event Store (Postgres)         ↓ analytics-worker         ↓ [Project 2] Snapshot (current_batch_state)         ↓ [Project 3] Analytics Map API         ↓ frontend (MapLibre)         ↓ [Project 5] Popup + CSV export

---

## 3. Компоненты системы

---

### 3.1 Project №1 — OLTP

Назначение:

- хранение текущего состояния
- быстрый доступ
- источник данных для внешних систем

Особенности:

- current state only
- без истории
- используется для операционной работы

---

### 3.2 Project №4 — Ingestion Pipeline

Назначение:

- доставка событий в analytics

Компоненты:

- MS SQL (source)
- mssql-extractor
- ingest API

Особенности:

- batch обработка
- retry
- DLQ
- cursor-based ingestion

---

### 3.3 Project №2 — Event & Snapshot

Назначение:

- построение аналитического слоя

Компоненты:

- event store (append-only)
- analytics worker
- snapshot (current_batch_state)

Инварианты:

- event store = source of truth
- snapshot = производная

---

### 3.4 Project №3 — Analytics Map

Назначение:

- визуализация данных

Источник:

- snapshot
- warehouses (география)

Особенности:

- агрегаты по складам
- один endpoint
- независимость от OLTP

---

### 3.5 Project №5 — Warehouse Popup

Назначение:

- drill-down аналитика

Функции:

- metadata склада
- агрегаты (count, sum)
- распределение по статусам
- CSV экспорт партий

Особенности:

- отдельный API
- не перегружает map endpoint

---

## 4. Поток данных

### 4.1 Источник

OLTP → MS SQL

---

### 4.2 Ingestion

MS SQL → extractor → ingest API → event store

---

### 4.3 Обработка

event store → worker → snapshot

---

### 4.4 Аналитика

snapshot → aggregation → map API

---

### 4.5 Drill-down

map click → popup API → CSV export

---

## 5. Источники истины

| Слой | Источник |
|-----|--------|
| Events | inventory_status_events |
| Snapshot | current_batch_state |
| География | analytics.warehouses |
| UI | analytics API |

---

## 6. Разделение ответственности

| Слой | Ответственность |
|------|----------------|
| OLTP | операционные данные |
| Ingestion | доставка данных |
| Event Store | история |
| Worker | обработка |
| Snapshot | текущее состояние |
| API | агрегация |
| Frontend | отображение |

---

## 7. Инварианты системы

1. event store — единственный источник истины
2. snapshot всегда производный
3. worker обрабатывает события по порядку
4. map API не зависит от OLTP
5. popup не влияет на map API
6. frontend не содержит бизнес-логики

---

## 8. API слой

### Map API

GET /api/analytics/map

---

### Popup API

GET /api/analytics/warehouse/{warehouse_id}

---

### CSV API

GET /api/analytics/warehouse/{warehouse_id}/batches.csv

---

### Ingest API

POST /api/analytics/ingest/events

---

## 9. Производительность

Подходы:

- batch processing
- snapshot вместо live aggregation
- один SQL для агрегатов
- chunking в ingestion
- streaming для CSV

---

## 10. Ограничения

1. нет кеширования
2. нет realtime UI
3. один worker
4. нет pagination в CSV
5. ограниченный горизонт событий

---

## 11. Trade-offs

| Решение | Почему |
|--------|--------|
| snapshot | быстрее чтение |
| Python aggregation | проще |
| без ORM | контроль |
| отдельный popup API | масштабируемость |

---

## 12. Расширение системы

Можно добавить:

- кеширование popup
- async export (S3)
- фильтры по партиям
- realtime обновление
- multi-worker processing

---

## 13. Итог

Система реализует:

- event-driven архитектуру
- аналитический слой
- визуализацию данных
- drill-down до уровня партий

---

## 14. Уровень системы

Архитектура соответствует:

- production-ready backend
- scalable analytics pipeline
- clean layered design

---

Система построена как единое целое,
без нарушения принципов между проектами.