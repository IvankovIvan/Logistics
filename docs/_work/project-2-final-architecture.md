# file: docs/project-2-final-architecture.md
Project №2 — Final Architecture

Declarative Warehouse Analytics Platform

⸻

1. Статус документа

Этот документ фиксирует окончательное архитектурное решение Project №2.

После утверждения:
	•	архитектура считается замороженной
	•	изменения возможны только через отдельное архитектурное решение
	•	Project №1 остаётся неизменяемым

⸻

2. Принципиальная позиция

Project №2:
	•	не расширяет Project №1
	•	не изменяет Project №1
	•	строится поверх него
	•	реализуется как отдельный доменный слой
	•	использует ту же БД
	•	использует отдельную schema analytics

⸻

3. Цель системы

Создать декларативную аналитическую платформу для складов, где:
	•	метрика выбирается пользователем
	•	период выбирается пользователем
	•	радиус кодирует агрегированное значение
	•	масштаб percentile-based
	•	агрегация динамическая
	•	метрики расширяемые без изменения фронта

⸻

4. Архитектурные инварианты

4.1 Разделение доменов
public      → Project №1 (current-state)
analytics   → Project №2 (analytics layer)

Project №1 не зависит от Project №2.

Project №2 может читать данные из public.

⸻

4.2 Grain модели

warehouse_fact

Grain:
(warehouse_id, date, metric_id)

Одна запись на склад, на день, на метрику.

⸻

4.3 Семантика overwrite

Если приходит событие с тем же:
warehouse_id
date
metric_id

И event_time ≥ last_event_time

→ значение перезаписывается.

Если event_time < last_event_time

→ событие считается stale.

⸻

5. Data Layer

5.1 analytics.metrics_catalog

Назначение: декларативное управление метриками.

Поля:
	•	metric_id (PK)
	•	name
	•	aggregation_type (sum | avg)
	•	unit
	•	scale_lower_percentile
	•	scale_upper_percentile
	•	enabled (boolean)

Инварианты:
	•	0 ≤ lower < upper ≤ 1
	•	metric_id обязателен для ingest
	•	enabled влияет только на read-side

Управление: вручную через SQL.

⸻

5.2 analytics.warehouse_fact

Назначение: хранение атомарных дневных значений.

Поля:
	•	warehouse_id (TEXT)
	•	date (DATE)
	•	metric_id (TEXT)
	•	value (BIGINT)
	•	last_event_time (TIMESTAMPTZ)

Ограничения:
	•	UNIQUE (warehouse_id, date, metric_id)
	•	INDEX (metric_id, date)

FK отсутствует (слабая связность).

⸻

5.3 analytics.analytics_ingest_events

Назначение: идемпотентность write-side.

Поля:
	•	event_id (PK)
	•	event_time (TIMESTAMPTZ)
	•	received_at (TIMESTAMPTZ default now())

Поведение:
	•	INSERT … ON CONFLICT DO NOTHING
	•	duplicate определяется по rowcount
	•	stale определяется через last_event_time

⸻

6. Write Layer

Endpoint:
POST /api/analytics/ingest

Требования:
	•	строгая идемпотентность
	•	metric_id обязан существовать
	•	overwrite по grain
	•	stale detection
	•	enabled не проверяется
	•	атомарная транзакция на batch

⸻

7. Read Layer

Endpoint:
GET /api/analytics/map

Параметры:
	•	metric_id (required)
	•	start_date (required)
	•	end_date (optional, default = today)

⸻

7.1 Семантика агрегации
SUM(value)

Если aggregation_type = avg:
SUM(value) / period_days

где:
period_days = end_date - start_date + 1


⸻

7.2 Покрытие складов

Всегда возвращаются все склады из:
public.warehouses_current

LEFT JOIN с warehouse_fact.

Если данных нет:

value = 0


⸻

7.3 Percentile scaling

Percentile считается:
	•	только по складам, где value > 0
	•	на агрегированных значениях

Используется:
percentile_cont(lower)
percentile_cont(upper)


⸻

7.4 Fallback стратегия

Если:
	•	count(value > 0) < 2
или
	•	lower == upper

Тогда:

lower = min(value > 0)
upper = max(value > 0)

Если min == max:
	•	используется фиксированный диапазон
	•	нулевые склады остаются нулевыми

⸻

8. Frontend инварианты

Frontend:
	•	получает raw values
	•	получает lower_percentile_value
	•	получает upper_percentile_value
	•	нормализует радиус
	•	не агрегирует
	•	не считает percentile
	•	не вычисляет формулы

Смена метрики не сбрасывает период.

⸻

9. Запрещено в Project №2
	•	materialized views
	•	производные формулы
	•	SQL expression engine
	•	BI-отчёты
	•	history versioning
	•	admin UI
	•	изменение /api/map

⸻

10. Инициализация БД

Analytics создаётся через:

db/init_analytics.sql

Выполняется при первичной инициализации БД.

Schema:

CREATE SCHEMA analytics;

Project №1 (db/init.sql) не изменяется.

⸻

11. Эволюция в будущем

Допустимые будущие расширения:
	•	добавление processed_at
	•	добавление audit статусов
	•	NUMERIC вместо BIGINT
	•	отдельная БД
	•	admin endpoint для metrics_catalog

Эти изменения не должны нарушать текущие инварианты.

⸻

12. Итоговое состояние

Project №2 является:
	•	декларативной
	•	расширяемой
	•	масштабируемой
	•	изолированной
	•	percentile-based
	•	динамической
	•	совместимой с Project №1

Архитектура заморожена.


