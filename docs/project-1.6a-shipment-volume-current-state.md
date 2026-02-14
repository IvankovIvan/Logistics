# Project №1.6.a — Shipment Volume as Current-State

Проект: Logistics  
Репозиторий: https://github.com/IvankovIvan/Logistics  

Контекст:
Project №1.1–1.5 завершены.
Quantity складов реализован как first-class current-state (Project №1.4).
Project №1.6 — расширение current-state маршрутов.

---

## 🎯 Цель этапа

Сделать volume (текущее количество товара “в пути сейчас”)
first-class current-state полем маршрута (shipment_current),
достаточным для визуальных инвариантов маршрутов (Project №1.6.b).

Без аналитики.  
Без истории.  
Без расчётов на read-side.  
Без нарушения архитектуры Project №1.

---

## 📦 Архитектурная модель

Система симметрична:

| Сущность | Поле      | Семантика                    |
|-----------|-----------|------------------------------|
| warehouses_current | quantity | сколько сейчас лежит |
| shipments_current  | volume   | сколько сейчас в пути |

Обе величины:
- абсолютные (не дельта),
- current-state,
- задаются write-side,
- не считаются на read-side,
- не агрегируются на frontend.

---

## 🗄️ Изменения модели данных

Таблица:
`shipments_current`

Добавляется поле:
volume INTEGER NOT NULL

Инварианты:
- volume ≥ 0
- отсутствие volume невозможно
- NULL запрещён
- отрицательные значения запрещены

---

## 🔌 Ingest семантика

ShipmentUpsertPayload теперь требует поле:
volume: int (required)

Классификация результата ingest остаётся прежней:

1. duplicate — event_id уже обработан
2. rejected — неподдерживаемый entity_type или отсутствие volume
3. applied — UPSERT применился (rowcount > 0)
4. stale — event_time устарел, volume не обновляется

Stale и idempotency логика не меняются.

---

## 📡 Read-side

/api/map расширяется:

MapRoute получает обязательное поле:
volume: int
Read-side:
- не вычисляет volume,
- не агрегирует,
- не трансформирует,
- просто прокидывает значение из current-state.

Отсутствие volume = контрактная ошибка.

---

## 🎨 Визуальные последствия (Project №1.6.b)

volume будет кодироваться:
- толщиной линии маршрута
- (опционально) подписью по центру линии

Геометрия не меняется.
Offset логика Project №1.3 сохраняется.

---

## 🔒 Инварианты системы

✔ система остаётся “витриной на сейчас”  
✔ нет истории  
✔ нет аналитики  
✔ нет расчётов на read-side  
✔ нет вычислений на frontend  
✔ маршруты остаются 1 shipment = 1 feature  
✔ Project №1.1–1.5 не нарушаются  

---

## 📍 Definition of Done

- volume хранится в shipments_current
- ingest требует volume
- stale semantics не изменены
- /api/map возвращает volume
- frontend получает volume без вычислений
- тесты зелёные
- контракт стабилен

---

## 📌 Статус

Project №1.6.a — ARCHITECTURE FIXED  
Готов к реализации.