# /opt/Logistics/docs/_work/project-2-v2-implementation.md
# 📘 Project №2 — Event & Snapshot Architecture (V2 Implementation)

---

## 1. Общая идея

Project №2 реализует event-driven аналитический слой поверх OLTP (Project №1).

Система построена по принципу:

```
events → processing → snapshot
```

Где:

* `inventory_status_events` — источник истины
* `analytics-worker` — процесс обработки
* `current_batch_state` — текущее состояние

---

## 2. Архитектурный поток

```
OLTP → /api/analytics/ingest/events → inventory_status_events
                                           ↓
                                    analytics-worker
                                           ↓
                                 current_batch_state
                                           ↓
                                     Read API (будет)
```

Дополнительно:

```
inventory_status_events → rebuild → current_batch_state
```

---

## 3. Основные компоненты

### 3.1 Event Store

Таблица: `analytics.inventory_status_events`

Характеристики:

* append-only
* partition by `event_time` (по месяцам)
* источник истины
* idempotency через `(operation_id, event_time)`

---

### 3.2 Snapshot

Таблица: `analytics.current_batch_state`

* содержит только активные партии
* обновляется только worker’ом
* полностью производная

---

### 3.3 Ingest API

Endpoint:

```
POST /api/analytics/ingest/events
```

Функции:

* принимает события
* пишет в event store
* гарантирует idempotency
* не обновляет snapshot

---

### 3.4 Analytics Worker

Файл:

```
app/workers/analytics_worker.py
```

Функции:

* читает события по `event_id`
* обрабатывает batch
* обновляет snapshot
* обновляет watermark

---

### 3.5 Rebuild

Файл:

```
app/services/analytics_rebuild/service.py
```

Функции:

* полностью пересобирает snapshot
* используется для проверки и восстановления

---

### 3.6 Consistency Check

Файл:

```
app/services/analytics_rebuild/consistency_check.py
```

Функции:

* сравнивает snapshot:

  * до rebuild
  * после rebuild
* гарантирует корректность системы

---

## 4. Инварианты системы

1. `inventory_status_events` — единственный источник истины
2. `current_batch_state` — всегда производная
3. worker обрабатывает события строго по `event_id`
4. snapshot обновляется только если событие новее
5. финальность определяется через `status_reason`
6. rebuild даёт тот же результат, что worker
7. нет UPDATE/DELETE в event_table

---

## 5. Idempotency

Гарантируется через:

```
(operation_id, event_time)
```

Контракт:

* `operation_id` уникален
* `event_time` НЕ меняется при ретраях

---

## 6. Обработка событий

### Финальное событие

```
DELETE FROM current_batch_state
WHERE batch_id = ?
AND last_event_time < event_time
```

---

### Не финальное событие

```
UPSERT (batch_id)
WHERE event_time > last_event_time
```

---

## 7. Late Events

Если:

```
event_time <= last_event_time
```

→ событие игнорируется

---

## 8. Watermark

Таблица:

```
analytics.worker_state
```

Правила:

* обновляется только после успешного batch
* монотонный (через GREATEST)
* защищён через FOR UPDATE

---

## 9. Производительность

Оптимизации:

* batch processing (worker)
* JOIN вместо N+1
* partitioning event table
* batch ingest (см. раздел 10)

---

## 10. Ingest Pipeline (реализация)

### 10.1 Общая модель

```
events →
    validate →
    create partitions →
    batch insert →
        success → fast path
        error   → fallback (safe path)
```

---

### 10.2 Валидация

Проверка диапазона выполняется в приложении (Python):

```
[now() - 6 months, now() + 1 month]
```

Если вне диапазона:

→ событие получает статус `rejected`

---

### 10.3 Управление партициями

Партиции создаются автоматически:

* по месяцам
* через функцию `analytics.create_month_partition()`
* batch-режим (1 раз на месяц, не на событие)

Свойства:

* idempotent (`CREATE TABLE IF NOT EXISTS`)
* безопасно при race condition

---

### 10.4 Batch Insert (fast path)

Используется:

```
INSERT ... VALUES (...), (...), (...)
ON CONFLICT (operation_id, event_time) DO NOTHING
RETURNING operation_id
```

Поведение:

* вставленные строки → `applied`
* отсутствующие в RETURNING → `duplicate`

---

### 10.5 Fallback (safe path)

При ошибке batch insert:

```
SAVEPOINT per event →
INSERT →
ROLLBACK TO SAVEPOINT при ошибке
```

Свойства:

* гарантирует обработку каждого события
* batch не падает
* сохраняет корректность

---

### 10.6 Итог ingest

Система реализует:

```
fast path (batch)
+
safe fallback (per-event)
```

---

## 11. Rebuild логика

Используется:

```
DISTINCT ON (batch_id)
ORDER BY event_time DESC, event_id DESC
```

Фильтр:

```
is_tracking_finished = false
```

---

## 12. Гарантия корректности

Проверка:

```
snapshot_before
vs
snapshot_after_rebuild
```

Через:

```
EXCEPT
```

---

## 13. Deployment

Worker запускается как отдельный сервис:

```
analytics-worker (docker)
```

Свойства:

* singleton
* restart: always
* независим от API

---

## 14. Ограничения

1. Late events не меняют snapshot
2. Требуется корректный `status_reason`
3. Только один worker
4. Rebuild может быть дорогим
5. Batch insert может fallback'иться при ошибках

---

## 15. Итог

Система реализует:

* event sourcing
* deterministic snapshot
* rebuildable state
* strict data consistency
* масштабируемый ingest pipeline

---

## 16. Статус

| Компонент         | Статус |
| ----------------- | ------ |
| Ingest            | ✔      |
| Event Store       | ✔      |
| Worker            | ✔      |
| Snapshot          | ✔      |
| Rebuild           | ✔      |
| Consistency Check | ✔      |
| Batch Ingest      | ✔      |

---

**Архитектура V2 реализована полностью.**
