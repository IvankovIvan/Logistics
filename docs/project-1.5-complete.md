# Project №1.4–1.5 — Quantity & Warehouses Visual Semantics

Проект: Logistics  
Репозиторий: https://github.com/IvankovIvan/Logistics  

Статус: COMPLETED  
Дата фиксации: <указать дату>

---

## Контекст

Project №1.1–1.3 были завершены ранее.  
Project №1.4–1.5 устраняли архитектурный блокер визуальной семантики складов.

Цель:  
Сделать quantity first-class current-state полем и корректно реализовать визуальную семантику складов без нарушения инвариантов витрины “на сейчас”.

---

# ✅ Project №1.4 — Quantity as Current-State

## Архитектурное решение

quantity = абсолютное значение current-state склада.  
Источник истины — write-side warehouse event.

Read-side и frontend ничего не считают.

## Реализация

- warehouses_current расширена полем quantity (NOT NULL)
- ingest требует quantity
- absence of quantity → rejected
- stale → quantity не меняется
- duplicate → ignore
- applied → overwrite quantity
- /api/map возвращает MapWarehouse.quantity (обязательное поле)

## Инварианты сохранены

- система остаётся витриной “на сейчас”
- нет аналитики
- нет истории
- idempotency и stale semantics неизменны
- маршруты не затронуты

---

# ✅ Project №1.5.a — Warehouses Geometry

## Цель

Кодировать quantity исключительно радиусом circle-layer.

## Формула

radius = clamp(
  minR + k * log10(quantity + 1),
  minR,
  maxR
)

Реализация через MapLibre expression.

## Реализовано

- buildWarehouseRadiusExpression()
- централизованные константы
- transform.ts не содержит логики радиуса
- hover складов отключён
- склады остаются под маршрутами

## Инварианты

- quantity ≥ 0 всегда отображается
- quantity = 0 не пропадает
- большие значения не доминируют
- цвет не кодирует quantity
- нет интерактивности
- нет аналитики

---

# ✅ Project №1.5.b — Warehouses Labels Semantics

## Реализация

Один symbol-layer для складов.

Zoom-based поведение через step(["zoom"], ...)

### Поведение:

Z < 5  
→ без текста

5 ≤ Z < 6.5  
→ №{id}

Z ≥ 6.5  
→

№{id} {name}  
{quantity}

## Особенности

- используется format + get
- текст справа от круга
- единый фиксированный offset
- без feature-state
- без hover
- без изменения transform.ts
- без изменения backend

---

# 🧱 Архитектурное состояние системы

Система:

- имеет честный current-state quantity
- геометрия складов устойчива
- подписи масштабируются по zoom
- маршруты полностью изолированы
- frontend не содержит бизнес-логики
- backend остаётся чистым
- визуальные инварианты стабильны

---

# 📍 Итоговый статус

Project №1.4 — COMPLETED  
Project №1.5.a — COMPLETED  
Project №1.5.b — COMPLETED  

Следующий этап: развитие маршрутов / аналитики / SLA (вне текущего scope)