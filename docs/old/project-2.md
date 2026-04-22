Project №2 — Analytics Layer (Final Architecture)

⸻

1. Цель

Project №2 — это изолированный аналитический слой поверх Project №1 (OLTP).

Назначение:
	•	хранить историю по складам
	•	считать метрики
	•	поддерживать периоды (день / неделя / произвольный диапазон)
	•	поддерживать состояние «сейчас»
	•	не нагружать OLTP-базу
	•	обеспечивать архитектурную изоляцию

Analytics не читает OLTP напрямую во время запроса пользователя.

⸻

2. Общая архитектура

Контейнеры
	1.	project1-db (OLTP)
	2.	analytics-db (PostgreSQL, отдельный volume)
	3.	analytics-worker (микро-batch процесс)

⸻

3. Поток данных

Client → Project 1 ingest → project1-db

analytics-worker (каждые ~60 секунд):
	1.	читает новые события из project1 event_log
	2.	трансформирует их
	3.	пишет агрегаты в analytics-db
	4.	обновляет watermark

Frontend → /api/analytics/map → analytics-db

OLTP и Analytics полностью изолированы.

⸻

4. Data Layer (analytics-db)

4.1 Schema

CREATE SCHEMA IF NOT EXISTS analytics;

⸻

4.2 metrics_catalog

Назначение: декларативное управление метриками.

Поля:
	•	metric_id TEXT PRIMARY KEY (slug, regex ^[a-z0-9_]{1,50}$)
	•	name TEXT NOT NULL
	•	aggregation_type TEXT CHECK (sum | avg)
	•	unit TEXT NOT NULL
	•	scale_lower_percentile DOUBLE PRECISION [0,1]
	•	scale_upper_percentile DOUBLE PRECISION [0,1]
	•	enabled BOOLEAN DEFAULT TRUE

Инварианты:
	•	lower < upper
	•	slug enforced

⸻

4.3 warehouse_fact

Grain:
(warehouse_id, date, metric_id)

Поля:
	•	warehouse_id TEXT NOT NULL
	•	date DATE NOT NULL
	•	metric_id TEXT NOT NULL
	•	value BIGINT CHECK (value >= 0)
	•	last_event_time TIMESTAMPTZ NOT NULL

PRIMARY KEY (warehouse_id, date, metric_id)

FOREIGN KEY (metric_id)
REFERENCES analytics.metrics_catalog(metric_id)
ON DELETE RESTRICT

⸻

Индексы
	1.	Для агрегаций по периоду:
(metric_id, date)
	2.	Для выборки по складу:
(warehouse_id)
	3.	Для получения “сейчас”:
(warehouse_id, metric_id, date DESC)

⸻

4.4 analytics_ingest_events

Назначение: идемпотентность.

Поля:
	•	event_id UUID PRIMARY KEY
	•	event_time TIMESTAMPTZ NOT NULL
	•	received_at TIMESTAMPTZ DEFAULT now()

⸻

5. Write Layer (analytics ingest)

Валидации:
	•	UUID event_id
	•	запрет future date
	•	проверка существования metric_id
	•	проверка enabled
	•	stale protection (event_time >= last_event_time)
	•	value >= 0

Статусы событий:
	•	applied
	•	stale
	•	duplicate
	•	rejected

⸻

6. Read Layer

Endpoint: GET /api/analytics/map

Поддержка режимов:
	•	сейчас → MAX(date)
	•	день → date = X
	•	неделя → SUM по диапазону
	•	период → SUM по диапазону

Агрегация определяется aggregation_type (sum | avg).

Всегда возвращаются все склады.

⸻

7. “Сейчас”

Определяется как:
MAX(date) для warehouse_id + metric_id

Не используется CURRENT_DATE.

⸻

8. Event Model

Project 1 содержит append-only event_log.

analytics-worker читает:
SELECT * FROM event_log
WHERE id > last_processed_id
ORDER BY id
LIMIT N

Это обеспечивает:
	•	строгий порядок
	•	корректный watermark
	•	возможность replay

⸻

9. Принципы архитектуры
	•	Полная изоляция OLTP и Analytics
	•	Нет прямых join между БД
	•	Нет runtime-зависимости
	•	Почти real-time через микро-batch
	•	Простая модель (без star-schema)
	•	Возможность эволюции

⸻

10. Что сознательно НЕ делаем
	•	Нет dimension-таблиц
	•	Нет hourly фактов
	•	Нет snapshot CSV
	•	Нет Kafka
	•	Нет двухфазных транзакций
	•	Нет soft-delete

⸻

11. Итог

Project №2 — это изолированный, event-driven, read-optimized аналитический слой с поддержкой:
	•	нескольких метрик одновременно
	•	разных периодов
	•	состояния “сейчас”
	•	высокой производительности
	•	масштабируемости

Архитектура заморожена.