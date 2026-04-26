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

Backend слой:

router  
→ service  
→ repository  
→ DB

Пояснение:

- repository (query layer) отвечает за доступ к данным
- service содержит только orchestration
- SQL не находится в service

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

### Frontend слой

Frontend архитектура:

component  
→ facade  
→ API layer  
→ backend

Где:

- component — UI слой (React)
- facade — orchestration, не делает HTTP
- API layer — все HTTP вызовы (fetch/axios)
- backend — FastAPI

Инварианты:

- fetch не используется вне API layer
- facade не делает HTTP
- все API вызовы централизованы

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

---

## Data Contract

Система использует единый контракт данных:

см. system-data-contract.md

Контракт определяет:
- структуру данных
- типы полей
- инварианты
- API формат

Является источником истины для:
- backend
- frontend
- ingestion pipeline

---

# ⚙️ Runtime & Environment (обязательно)

---

## 0. Project Root (обязательно)

Абсолютный путь проекта:

	/opt/Logistics

Правила:

- все команды выполняются относительно этого пути
- все ссылки в документации предполагают этот root
- все скрипты и docker используют этот путь

---

Примеры:

cd /opt/Logistics

docker compose up --build -d

docs находятся в:

/opt/Logistics/docs/

---

## 1. Docker Services

Система запускается через docker-compose.

Основные сервисы:

- app (FastAPI backend)
- nginx (reverse proxy)
- postgres (analytics DB)
- redis
- mssql-extractor (worker)
- analytics-worker

---

## 2. Ports

- backend: http://localhost:8000
- swagger: http://localhost:8000/docs
- nginx: http://localhost:80
- postgres (analytics): localhost:5433
- redis: localhost:6379

---

## 3. Запуск системы

Команда:

	docker compose up --build -d

Проверка:

	docker compose ps

---

## 4. Основные endpoints

- GET /api/analytics/map
- GET /api/analytics/warehouse/{id}
- GET /api/analytics/warehouse/{id}/batches.csv
- POST /api/analytics/ingest/events

Swagger:

	/docs

---

## 5. Переменные окружения

Основные env:

- MSSQL_BATCH_SIZE
- MSSQL_CHUNK_SIZE
- MSSQL_SLEEP_SECONDS
- MSSQL_MAX_RETRIES
- MSSQL_RETRY_DELAY
- MSSQL_HTTP_TIMEOUT

Назначение:

- управление ingestion pipeline (Project №4)

---

## 6. Workers

- analytics-worker:
  - обновляет snapshot
  - читает event store

- mssql-extractor:
  - читает MS SQL
  - отправляет события в ingest API

---

## 7. Инварианты runtime

- backend не работает без postgres
- ingestion независим от frontend
- workers работают отдельно
- API всегда читает из snapshot

---

## 8. Ошибки и диагностика

Проверка логов:

	docker compose logs app
	docker compose logs analytics-worker
	docker compose logs mssql-extractor

---

## 9. Быстрый reset

(если система сломалась)

	docker compose down -v
	docker compose up --build -d