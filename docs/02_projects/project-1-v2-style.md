
# /opt/Logistics/docs/_work/project-1-v2-style.md
# 📘 Project №1 — OLTP Map & Current State Architecture (V2 Style)

---

## 1. Цель

Project №1 — это OLTP слой системы логистики.

Назначение:

* хранить текущее состояние складов
* хранить текущее состояние перемещений
* обеспечивать быстрый доступ к данным для карты
* предоставлять Read API для фронтенда

---

## 2. Общая архитектура

```
OLTP → current tables → /api/map → frontend (MapLibre)
```

Описание потока:

1. Система обновляет текущие таблицы состояния.
2. API читает данные напрямую из текущих таблиц.
3. Данные передаются на фронтенд.
4. Фронтенд визуализирует карту.

---

## 3. Принципы

* Current state only (без истории)
* Быстрые чтения
* Простая модель данных
* Прямая зависимость от OLTP
* Минимальная обработка на backend
* Визуализация на frontend

---

## 4. Таблица: warehouses_current

Назначение: текущее состояние складов

Поля:

* id TEXT PRIMARY KEY
* name TEXT NOT NULL
* status TEXT NOT NULL
* location geometry(Point, 4326) NOT NULL
* quantity BIGINT NOT NULL
* last_event_time TIMESTAMPTZ NOT NULL
* updated_at TIMESTAMPTZ NOT NULL

---

## 5. Таблица: shipments_current

Назначение: текущее состояние перемещений

Поля:

* id TEXT PRIMARY KEY
* from_node TEXT NOT NULL
* to_node TEXT NOT NULL
* volume BIGINT NOT NULL

---

## 6. География

Используется PostGIS:

* geometry(Point, 4326)
* ST_X(location), ST_Y(location)
* ST_MakePoint(lon, lat)

---

## 7. Map API

Endpoint:

```
GET /api/map
```

Возвращает:

* warehouses
* routes

---

## 8. Формат ответа

warehouses:

* id
* name
* status
* lon
* lat
* quantity

routes:

* id
* from
* to
* volume
* coordinates

---

## 9. Логика карты

Карта отображает:

* текущее состояние (не историю)
* склады как точки
* маршруты как линии

Метрики:

* quantity → размер точки
* volume → толщина линии

---

## 10. Frontend

Используется:

* MapLibre
* GeoJSON
* polling обновления

---

## 11. Ограничения

1. Нет истории данных
2. Нет event sourcing
3. Нет rebuild
4. Прямая зависимость от OLTP
5. Ограниченная масштабируемость

---

## 12. Инварианты системы

1. warehouses_current — источник текущего состояния складов
2. shipments_current — источник текущих маршрутов
3. Карта всегда показывает текущее состояние
4. Геометрия хранится в PostGIS
5. Backend не агрегирует данные

---

## 13. Итог

Project №1 реализует:

* OLTP current-state модель
* географическую визуализацию
* базовый map API

---

Архитектура Project №1 зафиксирована.
