#docs/_work/project-2-v2-event-architecture.md

Project №2 — Event & Snapshot Architecture (V2)

⸻

1. Цель

Project №2 (V2) — это event-driven аналитический слой поверх Project №1.

Назначение:

* хранить полную историю движения партий
* поддерживать состояние «сейчас»
* обеспечивать операционный snapshot
* позволять rebuild без потери данных
* сохранять изоляцию от OLTP

Warehouse_fact временно отложен.

⸻

2. Общая архитектура

flowchart TD
    A[Project 1 OLTP] --> B[Ingest API]
    B --> C[inventory_status_events<br/>Append-Only<br/>Partitioned]
    C --> D[analytics-worker<br/>micro-batch]
    D --> E[current_batch_state<br/>Operational Snapshot]
    C -->|Rebuild| E
    E --> F[Read API<br/>/api/analytics/map]

Описание потока:

1. OLTP отправляет события в ingest API.
2. Ingest записывает события в event_table.
3. analytics-worker периодически считывает новые события.
4. Каждое событие:
    * уже находится в inventory_status_events
    * обновляет current_batch_state
5. Snapshot используется для быстрых чтений.
6. При необходимости snapshot может быть полностью пересобран из event_table.

⸻

3. Принципы

* Source of truth = inventory_status_events
* Append-only (никаких UPDATE / DELETE в event_table)
* Snapshot = производная таблица
* Без FK
* Минимум CHECK
* Бизнес-логика вне БД
* Финальность декларативная
* Масштабирование через partition

⸻

4. Таблица: inventory_status_events

Назначение: хранение полной истории изменений партии (batch).

Характеристики

* Partition by RANGE (event_time), шаг — месяц
* Append-only
* Источник истины

Поля

* event_id BIGSERIAL PRIMARY KEY
* batch_id BIGINT NOT NULL
* order_id BIGINT NOT NULL
* sku_id BIGINT NOT NULL
* warehouse_id BIGINT NOT NULL
* source_location_id BIGINT
* destination_location_id BIGINT
* status_id INT NOT NULL
* status_reason_id INT NOT NULL
* quantity BIGINT NOT NULL CHECK (quantity > 0)
* event_time TIMESTAMPTZ NOT NULL
* ingest_time TIMESTAMPTZ NOT NULL DEFAULT now()
* source_system INT NOT NULL
* operation_id BIGINT NOT NULL

Индексы
CREATE UNIQUE INDEX uniq_operation_id
ON analytics.inventory_status_events (operation_id);

CREATE INDEX idx_events_batch_time
ON analytics.inventory_status_events (batch_id, event_time DESC);

5. Финальность отслеживания

Финальность определяется через справочник status_reason.

В таблице status_reason есть поле:
is_tracking_finished BOOLEAN

Если TRUE — партия удаляется из snapshot.

Финальность не зашита в код.

⸻

6. Транзит

NULL не используется.

Для движения используется виртуальный склад:
TRANSIT_WAREHOUSE

warehouse_id всегда заполнен.

⸻

7. Таблица: current_batch_state

Назначение: хранит только активные партии.

Поля

* batch_id BIGINT PRIMARY KEY
* order_id BIGINT NOT NULL
* sku_id BIGINT NOT NULL
* warehouse_id BIGINT NOT NULL
* status_id INT NOT NULL
* quantity BIGINT NOT NULL
* source_location_id BIGINT
* destination_location_id BIGINT
* last_event_time TIMESTAMPTZ NOT NULL

Индекс
CREATE INDEX idx_current_batch_wh_status
ON analytics.current_batch_state (warehouse_id, status_id);

8. Ingest Pipeline

8.1 Модель доставки

Используется Push-модель.

OLTP отправляет события напрямую в ingest API.

⸻

8.2 Гарантия доставки

Гарантия: Exactly-once на уровне события.

Обеспечивается через уникальный operation_id.

Повторная отправка:

* не создаёт дубликат
* возвращает 200 OK

⸻

8.3 Поведение Ingest API

При получении события:

INSERT INTO inventory_status_events (...)
ON CONFLICT (operation_id) DO NOTHING;

Ingest API не обновляет snapshot напрямую.

⸻

9. analytics-worker

9.1 Режим работы

* Запуск по таймеру (например, раз в минуту)
* Micro-batch обработка
* Фиксированный batch size (конфигурируемый)

⸻

9.2 Offset / Watermark

Хранится в таблице:
CREATE TABLE analytics.worker_state (
    worker_name TEXT PRIMARY KEY,
    last_processed_event_id BIGINT NOT NULL
);

Worker читает:

SELECT *
FROM inventory_status_events
WHERE event_id > :last_processed_event_id
ORDER BY event_id
LIMIT :batch_size;

После успешной обработки батча:

UPDATE analytics.worker_state
SET last_processed_event_id = :max_event_id;

Offset обновляется только после успешной транзакции.

⸻

10. Логика обработки события

Для каждого события:

1. Событие уже сохранено в event_table.
2. Проверяется status_reason.is_tracking_finished.

Если TRUE:

DELETE FROM current_batch_state WHERE batch_id = ?;

Если FALSE:

* если записи нет → INSERT
* если event_time > last_event_time → UPSERT
* если event_time <= last_event_time → игнорировать

⸻

11. Rebuild Snapshot

Алгоритм:

1. Выбрать последнее событие по batch_id
2. Отфильтровать is_tracking_finished = false
3. Заполнить current_batch_state

Rebuild полностью повторяет логику worker.

⸻

12. Failure Scenarios

12.1 Duplicate Event

* Блокируется уникальным индексом
* Состояние не нарушается

12.2 Late Event

* Сохраняется в event_table
* Snapshot не обновляется

12.3 Worker Crash

* Offset не обновляется
* Батч перечитывается
* Модель остаётся идемпотентной

12.4 Rebuild Needed

* Snapshot очищается
* Пересобирается из event_table
* Финальные партии не включаются

⸻

13. Нагрузочная модель

Предположения:

* N партий в день
* 3–5 событий на партию
* Рост на 3+ года

inventory_status_events:

* append-only
* partition by month
* линейный рост
* старые партиции могут переводиться в read-only

current_batch_state:

* содержит только активные партии
* размер ограничен бизнес-потоком

Основная нагрузка:

* INSERT в event_table
* UPSERT / DELETE в snapshot
* чтение только из snapshot

⸻

14. Инварианты системы

1. inventory_status_events — единственный источник истины.
2. current_batch_state — полностью производная таблица.
3. warehouse_id никогда не NULL.
4. Финальность определяется только через status_reason.is_tracking_finished.
5. Snapshot содержит только активные партии.
6. Rebuild даёт тот же результат, что и live-processing.
7. Нет хардкода финальных статусов.
8. Нет runtime-зависимости от OLTP при чтении.

⸻

15. Trade-offs и ограничения

15.1 Нет FK

Осознанное решение:

* быстрее INSERT
* ниже связность
* контроль целостности в ingest

15.2 Нет soft-delete

* Snapshot содержит только активные партии
* История полностью в event_table

15.3 Нет Kafka

* Используется micro-batch
* Ниже сложность эксплуатации

15.4 Нет star-schema

* Система ориентирована на операционную аналитику
* BI-слой может быть добавлен в V3

15.5 Ограничения модели

1. Late events не меняют snapshot.
2. Коррекция задним числом требует rebuild.
3. Финальность зависит от корректности справочника.
4. Требуется строгий порядок обработки событий.

⸻

16. Статус

Event-table — зафиксирована
Snapshot — зафиксирован
Worker-логика — определена
Ingest pipeline — зафиксирован

Warehouse_fact — будет проектироваться отдельно (V3)

⸻

Архитектура V2 заморожена.