# /opt/Logistics/docs/_work/project-1-map-architecture.md

# 📘 Project №1 — Map & Current State Architecture

## 1. Общая идея
Project №1 реализует OLTP слой системы логистики и отвечает за текущее состояние складов и маршрутов.

Система построена вокруг:
- текущего состояния складов (warehouses_current)
- текущего состояния перемещений (shipments_current)
- API для отображения данных на карте

---

## 2. Архитектура

OLTP → current tables → /api/map → frontend (MapLibre)

---

## 3. Основные компоненты

### 3.1 Таблица warehouses_current
Назначение: хранит текущее состояние складов

Поля:
- id (PK)
- name
- status
- location (geometry Point, 4326)
- quantity
- last_event_time
- updated_at

---

### 3.2 Таблица shipments_current
Назначение: хранит текущие перемещения

Поля:
- id
- from_node (FK → warehouses_current)
- to_node (FK → warehouses_current)
- volume

---

### 3.3 Map API

Endpoint:
GET /api/map

Возвращает:
- warehouses (точки)
- routes (линии)

---

## 4. География

Используется PostGIS:
- geometry(Point, 4326)
- ST_X / ST_Y для извлечения координат
- ST_MakePoint для записи

---

## 5. Логика карты

Карта отображает:
- текущее состояние (не историю)
- склады (точки)
- маршруты (линии)

Метрики:
- quantity → размер точки
- volume → толщина линии

---

## 6. Frontend

Используется:
- MapLibre
- GeoJSON
- polling обновления

---

## 7. Ограничения

- зависимость от OLTP
- нет исторических данных
- нет rebuild
- агрегация ограничена

---

## 8. Итог

Project №1 реализует:
- OLTP current-state модель
- географическую визуализацию
- базовые метрики

Но:
- не поддерживает event sourcing
- не поддерживает rebuild
- зависит от текущих таблиц

