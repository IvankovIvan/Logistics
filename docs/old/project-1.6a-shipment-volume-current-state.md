Project №1.6.a — Shipment Volume as Current-State

Проект: Logistics
Репозиторий: https://github.com/IvankovIvan/Logistics
Статус: COMPLETED

⸻

🎯 Цель этапа

Добавить volume как first-class current-state поле для shipments_current, полностью симметрично warehouse.quantity (Project №1.4), без нарушения архитектуры Project №1.

Система должна оставаться:
	•	витриной “на сейчас”
	•	без истории
	•	без аналитики
	•	без агрегаций
	•	без вычислений на read-side
	•	с сохранением idempotency и stale semantics

⸻

🧱 Архитектурное решение

Принцип

volume — абсолютное текущее значение перевозки.
	•	Не дельта.
	•	Не вычисляется.
	•	Не агрегируется.
	•	Обновляется только через warehouse/shipment event.

Единственный источник истины — write-side ingest.

⸻

🗄️ Database

Таблица: shipments_current

Добавлено поле:
volume INTEGER NOT NULL
CONSTRAINT shipments_current_volume_check CHECK (volume >= 0)

Инварианты:
	•	NULL запрещён
	•	Отрицательные значения запрещены
	•	История отсутствует
	•	Таблица остаётся current-state only
	•	last_event_time защита сохранена

⸻

🔌 Ingest

ShipmentUpsertPayload

Добавлено обязательное поле:

volume: int
ge = 0

Поведение:

Сценарий    Результат
duplicate   ignore
rejected    unsupported entity
stale       volume не обновляется
applied     volume перезаписывается

SQL UPSERT не менялся концептуально:

WHERE shipments_current.last_event_time <= EXCLUDED.last_event_time

Idempotency полностью сохранена.

⸻

📖 Read-Side

Обновлены:
	•	SHIPMENTS_CURRENT SELECT
	•	PostgresDataSource
	•	FAKE_SHIPMENTS
	•	InMemoryIngestDataSource
	•	ShipmentLike protocol
	•	MapRoute модель
	•	map_builder

Правило:

Отсутствие volume — контрактная ошибка.

Никаких fallback.
Никаких вычислений.
Никаких агрегатов.

Read-side только прокидывает значение.

⸻

🌐 Контракт /api/map

MapRoute теперь содержит:

volume: int  (required)

Инварианты:
	•	volume ≥ 0
	•	volume обязательный
	•	отсутствие volume = ошибка
	•	никаких производных значений

⸻

🧪 Тестирование

Добавлены проверки:
	•	shipment без volume → rejected
	•	stale не меняет volume
	•	duplicate не меняет состояние
	•	applied обновляет volume
	•	read-model требует volume

Результат:

docker compose exec app pytest
→ все тесты зелёные

Инварианты Project №1 сохранены

✔ current-state only
✔ idempotency
✔ stale semantics
✔ отсутствие истории
✔ отсутствие аналитики
✔ /api/map — единственный публичный контракт
✔ frontend ничего не считает

⸻

🧱 Архитектурная симметрия

Сущность        Поле        Тип
warehouse       quantity    INTEGER
shipment        volume      INTEGER

Обе величины:
	•	абсолютные
	•	current-state
	•	first-class
	•	обновляются только через события
	•	не вычисляются на read-side
	•	не агрегируются

⸻

📦 Результат

После Project №1.6.a система имеет:
	•	quantity складов
	•	volume маршрутов
	•	полностью согласованный current-state контракт
	•	чистую симметрию сущностей
	•	готовность к визуализации маршрутов по объёму (Project №1.6.b)

⸻

🧠 Вывод

Project №1.6.a завершён без архитектурных компромиссов.

Система остаётся:
	•	минималистичной
	•	детерминированной
	•	масштабируемой
	•	без скрытой логики
	•	без аналитики
	•	без временных костылей

⸻

Статус:

Project №1.6.a — COMPLETED



