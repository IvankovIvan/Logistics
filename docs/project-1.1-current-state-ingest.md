Project №1.1 — Current-State DB + Ingest

Цель этапа

Реализовать хранение текущего состояния логистики (без истории) и идемпотентный ingest событий, не меняя контракт /api/map и не вовлекая фронт в события.

⸻

Архитектурные инварианты (соблюдены)
	•	Экран «на сейчас» (без аналитики и истории)
	•	Данные могут приходить в любом порядке
	•	Строгая идемпотентность ingest
	•	Frontend работает только с /api/map
	•	Read-side и write-side полностью разделены

⸻

Итоговая архитектура

Write-side (ingest)
	•	Endpoint: /api/ingest/batch
	•	Принимает события:
	•	event_id — уникальный ключ
	•	event_time — время события (UTC, секунды)
	•	entity_type — warehouse | shipment
	•	payload — opaque JSON

Гарантии:
	•	ingest_events защищает от повторов
	•	Старые события не перетирают новые (event_time >= last_event_time)

Read-side (map)
	•	Endpoint: /api/map
	•	Читает только current-state из источника данных
	•	Не знает про ingest, события и порядок доставки

Связь read/write — исключительно через БД.

⸻

Источники данных (DATA_SOURCE_MODE)

Реализован selector источников:
	•	fake — эталон / локальная разработка
	•	ingest_mem — in-memory ingest
	•	postgres — production read-side

Источник выбирается на момент запроса, без import-time side effects.

⸻

База данных (PostgreSQL + PostGIS)

Таблицы

1. ingest_events
	•	event_id (PK)
	•	entity_type
	•	entity_id
	•	event_time
	•	received_at

Назначение: идемпотентность (не event-store).

2. warehouses_current
	•	id (PK)
	•	name
	•	status
	•	location — POINT(4326)
	•	last_event_time
	•	updated_at

3. shipments_current
	•	id (PK)
	•	from_node → warehouses_current.id
	•	to_node → warehouses_current.id
	•	status
	•	last_event_time
	•	updated_at

История намеренно не хранится.

⸻

Read-side реализация

Структура:

services/data_sources/
├── base.py
├── selector.py
├── fake_data.py
├── fake.py
└── postgres/
    ├── connection.py
    ├── queries.py
    └── datasource.py

	•	map_builder не менялся
	•	Источник данных прозрачен для карты

⸻

Ingest реализация

Структура:

services/ingest/
├── models.py
├── queries.py
└── service.py
routers/ingest.py

	•	Batch ingest
	•	Синхронный write-side
	•	Подготовлено к Celery

⸻

Инфраструктура

Docker Compose включает:
	•	FastAPI
	•	Next.js
	•	Nginx
	•	PostgreSQL + PostGIS
	•	Redis

Добавлен db/init.sql — БД поднимается сразу готовой.

⸻

End-to-End подтверждение

Прогнан сценарий:

ingest (warehouse)
→ ingest (shipment)
→ PostgreSQL current-state
→ /api/map

Проверено:
	•	идемпотентность
	•	out-of-order защита
	•	стабильность /api/map

⸻

Статус

✅ Project №1.1 завершён

Система готова к:
	•	Celery / async ingest
	•	контрактным E2E тестам
	•	добавлению истории отдельным этапом
	•	Project №1.2