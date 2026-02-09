Project №1.4.d — Миграция quantity в current-state (DB + ingest контракт)

Цель
Зафиксировать, как quantity появляется в системе технически, не реализуя код и не ломая Project №1.1–1.3.

⸻

Что уже принято (контекст)
	•	Quantity — абсолютное значение.
	•	Источник истины — событие склада (warehouse).
	•	Read-side и фронт ничего не считают.
	•	/api/map остаётся витриной current-state.

⸻

Изменения на уровне модели (без реализации)

1️⃣ Current-state БД

Таблица: warehouses_current

Добавляется поле:
	•	quantity BIGINT NOT NULL

Семантика:
	•	хранит текущее абсолютное количество;
	•	обновляется вместе с остальными полями склада;
	•	подчиняется last_event_time.

⸻

2️⃣ Ingest payload (warehouse)

Событие entity_type = "warehouse" обязано содержать:
{
  "id": "warehouse_id",
  "quantity": number
}

Правила:
	•	отсутствие quantity → логическая ошибка (rejected);
	•	stale-событие → quantity не меняется;
	•	duplicate → игнорируется;
	•	applied → quantity перезаписывается.

⸻

3️⃣ Read-side (/api/map)

MapWarehouse расширяется:
	•	quantity: number

Read-side:
	•	не вычисляет;
	•	не агрегирует;
	•	просто читает warehouses_current.quantity.

⸻

Почему это не ломает систему
	•	ingest уже умеет:
	•	idempotency,
	•	stale-защиту,
	•	абсолютные значения;
	•	добавляется одно поле, без изменения потоков;
	•	маршруты, фильтры, визуал Project №1.3 не затрагиваются.

⸻

Границы подэтапа (жёстко)

❌ не добавляем supply/sale
❌ не трогаем shipments
❌ не меняем /api/map семантически
❌ не считаем “в пути”
❌ не делаем UI

⸻

Результат подэтапа

После Project №1.4.d:
	•	quantity архитектурно легализован,
	•	Project №1.5 (Warehouses Visual Semantics) разблокирован,
	•	можно честно переходить к визуалу складов.
