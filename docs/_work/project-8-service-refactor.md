# /opt/Logistics/docs/_work/project-8-service-refactor.md

# 📘 Project №8 — Service Layer Refactoring & API Contracts (V1)

## 1. Цель

Привести backend к production-уровню:

- стандартизировать service layer
- зафиксировать API контракты (Pydantic)
- убрать неявную типизацию
- устранить размазанную бизнес-логику

---

## 2. Область работ

Включает:

- app/services/*
- app/routers/*
- app/models/*

Не включает:

- ingestion pipeline (Project №4)
- event store (Project №2)
- snapshot
- database schema

---

## 3. Архитектурные принципы

Сохраняются:

router → service → DB

Дополнительно:

- service = одна ответственность
- router = без логики
- models:
  - request
  - response
  - internal

---

## 4. Ограничения

- services перегружены
- нет чёткого разделения логики
- слабая типизация psycopg
- возможны raw dict в API
- модели смешаны (API + внутренние)

---

## 5. План работ

### Step 1 — Audit services
- найти все сервисы
- определить их ответственность
- выявить нарушения архитектуры

---

### Step 2 — Classification
- разделить сервисы:
  - ingest
  - analytics
  - map
  - popup
- определить границы

---

### Step 3 — Refactor services
- разделить большие сервисы
- убрать лишнюю логику
- нормализовать SQL слой

---

### Step 4 — Models cleanup
- разделить модели:
  - request
  - response
  - internal
- убрать лишние

---

### Step 5 — API contracts
- везде response_model
- убрать dict
- привести Swagger к стандарту

---

### Step 6 — Final verification
- проверить API
- проверить Swagger
- проверить интеграцию frontend

---

## 6. Инварианты

- архитектура НЕ меняется
- ingestion НЕ трогается
- DB НЕ меняется
- каждый шаг → commit

---

## 7. Критерий успеха

- нет raw dict в API
- все endpoints имеют Pydantic
- services читаются как отдельные модули
- код предсказуем

---

## 8. Текущий state (Audit)

### analytics_map_builder.py
- ответственность:
  - сборка карты
  - metadata склада
  - метрики склада
  - CSV выгрузка
- таблицы:
  - analytics.warehouses
  - analytics.current_batch_state
  - analytics.cities
  - analytics.warehouse_types
  - analytics.status_dict
- проблемы:
  - большой файл (~345 строк)
  - смешение ответственности
  - SQL + агрегация + форматирование вместе
  - использование dict вместо моделей

---

### analytics_ingest/service.py
- ответственность:
  - ingest pipeline
  - batch insert
  - fallback
  - partition management
- таблицы:
  - analytics.inventory_status_events
- проблемы:
  - очень большой файл (~370 строк)
  - смешение логики
  - SQL builder внутри service
  - dict / Mapping вместо моделей

---

### analytics_ingest/connection.py
- ответственность:
  - подключение к Postgres
- проблемы:
  - используется не только ingest
  - фактически является общим DB layer

---

### analytics_rebuild/service.py
- ответственность:
  - rebuild snapshot
- таблицы:
  - analytics.current_batch_state
  - analytics.inventory_status_events
  - analytics.status_reason
- проблемы:
  - SQL + orchestration вместе

---

### analytics_rebuild/consistency_check.py
- ответственность:
  - проверка snapshot после rebuild
- таблицы:
  - analytics.current_batch_state
- проблемы:
  - SQL + логика проверки вместе
  - нет моделей

---

### Общие проблемы

- сервисы слишком крупные
- смешение ответственности
- слабая типизация
- отсутствие разделения на домены

---

## 9. Вывод

Текущий state сервисного слоя требует систематического переструктурирования:

- **Сервисы перегружены** — analytics_map_builder (345 строк) и analytics_ingest/service (370 строк) смешивают SQL, логику агрегации и форматирование ответов в одном модуле

- **Смешение ответственности** — каждый сервис решает слишком много задач (например, map_builder одновременно собирает карту, получает metadata, метрики и готовит CSV)

- **Слабая типизация** — повсеместное использование dict[str, object] и Mapping[str, Any] вместо Pydantic моделей осложняет поддержку и интеграцию с frontend

- **Структура рефакторинга определена** — план из 6 шагов (Audit → Classification → Refactor services → Models cleanup → API contracts → Verification) обеспечивает систематический переход к production-уровню с сохранением архитектурных инвариантов