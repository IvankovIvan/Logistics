📘 Project №2 — Event & Snapshot Architecture (V2 Implementation)

⸻

1. Общая идея

Project №2 реализует event-driven аналитический слой поверх OLTP (Project №1).

Система построена по принципу:
events → processing → snapshot

Где:

* inventory_status_events — источник истины
* analytics-worker — процесс обработки
* current_batch_state — текущее состояние

⸻

2. Архитектурный поток

OLTP → /api/analytics/ingest/events → inventory_status_events
                                           ↓
                                    analytics-worker
                                           ↓
                                 current_batch_state
                                           ↓
                                     Read API (будет)

Дополнительно:

inventory_status_events → rebuild → current_batch_state

⸻

3. Основные компоненты

3.1 Event Store

Таблица: analytics.inventory_status_events

Характеристики:

* append-only
* partition by event_time
* источник истины
* idempotency через (operation_id, event_time)

⸻

3.2 Snapshot

Таблица: analytics.current_batch_state

* содержит только активные партии
* обновляется только worker’ом
* полностью производная

⸻

3.3 Ingest API

Endpoint:

POST /api/analytics/ingest/events

Функции:

* принимает события
* пишет в event store
* гарантирует idempotency
* не обновляет snapshot

⸻

3.4 Analytics Worker

Файл:

app/workers/analytics_worker.py

Функции:

* читает события по event_id
* обрабатывает batch
* обновляет snapshot
* обновляет watermark

⸻

3.5 Rebuild

Файл:
app/services/analytics_rebuild/service.py

Функции:

* полностью пересобирает snapshot
* используется для проверки и восстановления

⸻

3.6 Consistency Check

Файл:
app/services/analytics_rebuild/consistency_check.py

Функции:

* сравнивает snapshot:
    * до rebuild
    * после rebuild
* гарантирует корректность системы

⸻

4. Инварианты системы

1. inventory_status_events — единственный источник истины
2. current_batch_state — всегда производная
3. worker обрабатывает события строго по event_id
4. snapshot обновляется только если событие новее
5. финальность определяется через status_reason
6. rebuild даёт тот же результат, что worker
7. нет UPDATE/DELETE в event_table

⸻

5. Idempotency

Гарантируется через:

(operation_id, event_time)

Контракт:

* operation_id уникален
* event_time НЕ меняется при ретраях

⸻

6. Обработка событий

Для каждого события:

Если финальное:

DELETE FROM current_batch_state
WHERE batch_id = ?
AND last_event_time < event_time
⸻

Если не финальное:

UPSERT (batch_id)
WHERE event_time > last_event_time

⸻

7. Late Events

Если:

event_time <= last_event_time


→ событие игнорируется

⸻

8. Watermark

Таблица:
analytics.worker_state

Правила:

* обновляется только после успешного batch
* монотонный (через GREATEST)
* защищён через FOR UPDATE

⸻

9. Производительность

Оптимизации:

* batch processing
* JOIN вместо N+1
* partitioning event table

⸻

10. Rebuild логика

Используется:

DISTINCT ON (batch_id)
ORDER BY event_time DESC, event_id DESC

И фильтр:

is_tracking_finished = false

⸻

11. Гарантия корректности

Система проверяется через:

snapshot_before
vs
snapshot_after_rebuild

Используется:

EXCEPT

⸻

12. Deployment

Worker запускается как отдельный сервис:

analytics-worker (docker)

Свойства:

* singleton
* restart: always
* независим от API

⸻

13. Ограничения

1. Late events не меняют snapshot
2. Требуется корректный status_reason
3. Только один worker
4. Rebuild может быть дорогим

⸻

14. Итог

Система реализует:

* event sourcing
* deterministic snapshot
* rebuildable state
* strict data consistency

⸻

15. Статус
Компонент

Статус

Ingest

✔

Event Store

✔

Worker

✔

Snapshot

✔

Rebuild

✔

Consistency Check

✔

⸻

Архитектура V2 реализована полностью.

