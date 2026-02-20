Project №2 — Analytics Layer (Warehouse Metrics Platform)

Статус

Draft → Architecture Locked
Расширяет систему поверх Project №1 без изменения его инвариантов.

⸻

1. Назначение

Project №2 превращает карту Logistics в универсальную аналитическую платформу,
где пользователь выбирает метрику и период,
а карта визуализирует агрегированные значения по складам.

Project №2:
	•	не изменяет Project №1
	•	не превращает current-state в BI
	•	не ломает /api/map
	•	добавляет отдельный аналитический слой

⸻

2. Концептуальная модель

Карта = универсальный визуальный движок
Метрика = декларативная сущность
Период = глобальный контекст

Радиус склада всегда кодирует выбранную метрику.

Current-state (quantity) становится одной из метрик.

⸻

3. Data Layer

3.1 warehouse_fact (Long Model)

Grain = день
Хранит атомарное агрегированное дневное значение.

warehouse_id
date
metric_id
value
last_event_time

Ограничение:

UNIQUE (warehouse_id, date, metric_id)

Семантика:
	•	одно значение на склад / дату / метрику
	•	overwrite допустим
	•	история версий не хранится

⸻

3.2 metrics_catalog

Метрика — first-class entity.

metric_id (PK)
name
aggregation_type (sum | avg)
unit
scale_strategy_type (percentile)
scale_percentile (int)
enabled (boolean)

Свойства:
	•	декларативная
	•	расширяемая
	•	хранится в БД
	•	управляется вручную через SQL (на старте)

3.3 analytics_ingest_events

Для строгой идемпотентности.

event_id (PK)
event_time
metric_id
warehouse_id
date
value
processed_at

Семантика:
	•	duplicate → event_id уже существует
	•	stale → event_time < last_event_time
	•	applied → UPSERT реально обновил факт
	•	rejected → логическая ошибка

4. Write Layer

Endpoint:

POST /api/analytics/ingest


Особенности:
	•	строгая идемпотентность
	•	UPSERT в warehouse_fact
	•	stale detection
	•	overwrite допустим
	•	контракт честный (applied / duplicate / stale / rejected)

⸻

5. Read Layer

Endpoint:

GET /api/analytics/map

Параметры:
	•	metric_id (обязательный)
	•	start_date (обязательный)
	•	end_date (optional → today если отсутствует)

Период:

start_date ≤ date ≤ end_date

Агрегация:
	•	SUM(value) или AVG(value)
	•	dynamic
	•	без materialized views

Percentile:
	•	рассчитывается через percentile_cont
	•	per metric
	•	динамически при каждом запросе

Fallback:
	•	если по складу нет данных → value = 0
	•	склад всегда возвращается

Ответ содержит:
	•	warehouse_id
	•	aggregated_value
	•	percentile_value
	•	metric_meta
	•	period_used
	•	last_updated

Backend возвращает raw данные.
Нормализацию радиуса выполняет frontend.

⸻

6. Frontend Layer

Радиус:
	•	зависит от выбранной метрики
	•	адаптивный к периоду
	•	percentile-based normalization
	•	рассчитывается на frontend

Поведение:
	•	смена метрики → период сохраняется
	•	смена периода → радиусы пересчитываются
	•	масштаб адаптивный

⸻

7. Масштабирование

Scale Strategy:
	•	type = percentile
	•	percentile задаётся per metric
	•	рассчитывается через percentile_cont

Это предотвращает визуальный перекос из-за экстремумов.

⸻

8. Инварианты Project №2
	•	Long fact-table
	•	Grain = день
	•	overwrite допустим
	•	строгая идемпотентность ingest
	•	динамическая агрегация
	•	percentile честный
	•	радиус = единственный визуальный канал
	•	адаптивный масштаб
	•	метрики декларативные
	•	каталог метрик хранится в БД
	•	frontend универсальный визуальный движок

⸻

9. Границы Project №2

Project №2 НЕ включает:
	•	производные формулы
	•	ratio-метрики
	•	произвольный SQL
	•	materialized views
	•	историю версий фактов
	•	admin UI
	•	BI / отчётность

Это чистый аналитический слой визуального сравнения складов.

⸻

10. Расширяемость

Будущие этапы могут добавить:
	•	производные метрики
	•	composite expressions
	•	admin endpoint
	•	materialized views
	•	маршрутную аналитику
	•	дополнительные визуальные каналы

Но не в рамках текущего этапа.

⸻

Итог

Project №2 — это:

Declarative Metric Engine
	•	Dynamic Aggregation
	•	Percentile-Based Visual Normalization
	•	Strict Idempotent Write Layer

Архитектура зафиксирована.