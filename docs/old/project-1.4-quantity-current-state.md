ИТОГИ PROJECT №1.4 — Quantity as Current-State

Контекст:
Project №1 — Logistics.
Репозиторий: https://github.com/IvankovIvan/Logistics
Project №1.1–1.3 закрыты и не тронуты.

Цель Project №1.4:
Сделать quantity (абсолютное текущее количество товара на складе)
first-class current-state полем, достаточным для /api/map,
не превращая систему в аналитику и не ломая существующие инварианты.

Что было выявлено:
- /api/map (MapWarehouse) не содержал quantity.
- quantity не хранился в current-state.
- ingest и read-side не могли обеспечить визуальные инварианты складов (Project №1.5 заблокирован).

Принятое архитектурное решение:
- quantity — first-class поле current-state склада.
- quantity = абсолютное значение (не дельта).
- Единственный источник истины — write-side warehouse event.
- Read-side и frontend ничего не считают и не агрегируют.
- absence of quantity = contract error (склад не должен попадать в /api/map).
- Stale / idempotency — без изменений (event_time, ingest_events).

Реализация Project №1.4:
- DB:
  - warehouses_current расширена полем quantity (NOT NULL).
- Ingest:
  - WarehouseUpsertPayload требует quantity.
  - absence of quantity → rejected.
  - stale → quantity не меняется.
  - duplicate → ignore.
  - applied → overwrite quantity.
- Current-state:
  - Все data_sources (postgres, fake, ingest_mem) обязаны отдавать quantity
    или явно ломаться (маскировка запрещена).
- /api/map:
  - MapWarehouse расширен обязательным полем quantity.
  - map_builder прокидывает quantity напрямую из current-state.
  - Склад без quantity не включается в ответ.
- Frontend:
  - Контракт /api/map обновлён (quantity обязателен).
  - transform.ts прокидывает quantity без вычислений.
- Инварианты Project №1.1–1.3 сохранены:
  - idempotency и stale semantics не изменены,
  - read-side без логики,
  - маршруты и визуал Project №1.3 не затронуты.

Проверка:
- Выполнено: `docker compose exec app pytest`
- Все тесты зелёные.

Результат:
- quantity легализован как first-class current-state поле.
- /api/map теперь достаточен для визуальных инвариантов складов.
- Project №1.5 (Warehouses Visual Semantics) разблокирован.

Статус:
Project №1.4 — ЗАКРЫТ.