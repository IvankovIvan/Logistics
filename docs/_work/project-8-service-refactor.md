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

---

## 10. Результат Step 3 — Classification

Сервисы разделены на логические домены:

### Map
- build_analytics_map_warehouses

Назначение:
- формирование данных для карты

---

### Warehouse (popup + CSV)
- get_analytics_warehouse_metadata
- get_analytics_warehouse_metrics
- get_analytics_warehouse_batches

Назначение:
- работа с конкретным складом
- popup данные
- CSV выгрузка

---

### Ingest
- ingest_analytics_events
- _add_months
- _month_start_utc
- _event_params
- _build_batch_insert_query
- _build_batch_params
- _insert_events_fallback_per_event

Назначение:
- обработка входящих событий
- запись в event store

---

### Rebuild
- rebuild_snapshot
- _run_rebuild
- check_snapshot_consistency
- _get_count

Назначение:
- пересборка snapshot
- проверка консистентности

---

### DB
- get_analytics_connection

Назначение:
- подключение к базе данных

---

## 11. Целевая структура сервисов

app/services/

    analytics/
        map/
        warehouse/

    ingest/

    rebuild/

    db/

---

## 12. Вывод

- функции успешно разделены по доменам
- устранена неявная структура service layer
- определена целевая архитектура
- можно переходить к безопасному рефакторингу

---

## 13. Результат Step 7 — Cleanup proxy

Удалены временные proxy-модули:

### Удалено
- analytics_ingest/connection.py
  - причина: отсутствуют использования
  - все импорты переведены на db слой

### Сохранено
- analytics_map_builder.py
  - причина: используется router'ом
  - является API-границей
  - будет удалён на следующем этапе (refactor router)

---

## 14. Текущая архитектура

router → analytics_map_builder (proxy) → map.service → db

warehouse.service → db  
ingest.service → db  
rebuild.service → db  

---

## 15. Вывод

- proxy слой частично устранён
- db слой централизован
- архитектура приведена к слоистой модели
- подготовлена база для рефакторинга router слоя

---

## 16. Step 8 — Router refactor

Цель:
- удалить analytics_map_builder как proxy слой
- перевести router напрямую на map.service

Изменение:

было:
router → analytics_map_builder → map.service → db

станет:
router → map.service → db

Причина:
- analytics_map_builder больше не содержит логики
- является лишним уровнем абстракции
- усложняет архитектуру

---

## 17. Ожидаемый результат

- удалён последний proxy слой
- упрощён вызов map API
- структура соответствует router → service → db