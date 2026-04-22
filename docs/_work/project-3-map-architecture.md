# /opt/Logistics/docs/_work/project-3-map-architecture.md
# 📘 Project №3 — Analytics Map Architecture (V1 Final, Clean)

---

## 1. Цель

Project №3 — визуализация аналитических данных (Project №2) на карте.

Назначение:

* отображать текущее состояние складов
* визуализировать агрегированные данные
* предоставить аналитический слой поверх snapshot
* быть полностью независимым от OLTP

---

## 2. Общая архитектура

```
analytics.current_batch_state → aggregation → map_builder → /api/analytics/map → frontend
```

Дополнительно:

```
analytics.warehouses → география и справочники
```

---

## 3. Источники данных

### 3.1 Snapshot (факты)

```
analytics.current_batch_state
```

Хранит:
* активные партии
* статус (`status_id`)
* количество (`quantity`)

⚠️ В V1:
* `status_reason_id` НЕ используется в карте

---

### 3.2 География (reference layer)

```
analytics.warehouses
```

Является master-таблицей складов.

Поля:

* `warehouse_id` — стабильный идентификатор
* `name` — название склада
* `city_id` — ссылка на справочник городов
* `warehouse_type_id` — тип склада
* `lat`, `lon` — координаты (WGS84)
* `created_at`, `updated_at` — технические поля

Особенности:

* не используется PostGIS
* полностью независима от OLTP
* единственный источник географии

---

### 3.3 Справочники

```
analytics.cities
analytics.warehouse_types
```

Назначение:

* нормализация данных
* исключение дублирования
* фильтрация и аналитика

---

## 4. Логика агрегации

```
GROUP BY warehouse_id, status_id
```

Источник:

```
analytics.current_batch_state
```

Результат:

* `total` — общий объём по складу
* `by_status` — распределение по статусам

⚠️ В V1:
* `by_reason` отсутствует

---

## 5. Объединение данных

```
analytics.warehouses
LEFT JOIN aggregation
```

Особенности:

* ВСЕ склады попадают в ответ
* пустые склады → `total = 0`
* реализовано в Python (map_builder)

---

## 6. API

```
GET /api/analytics/map
```

Особенности:

* новый endpoint
* один запрос
* полностью на analytics

---

## 7. Формат ответа

```
{
  "warehouses": [
    {
      "warehouse_id": 1,
      "name": "Склад",
      "lat": 59.93,
      "lon": 30.31,
      "metrics": {
        "total": 120,
        "by_status": [
          { "status_id": 1, "quantity": 50 },
          { "status_id": 2, "quantity": 70 }
        ]
      }
    }
  ],
  "routes": []
}
```

---

## 8. Визуализация

Карта отображает:

* точки складов
* агрегированные метрики
* интерактив (клик по складу)

Слои:

* общий объём (`metrics.total`)
* по статусам (`by_status`)

При клике на склад:

* отображается popup
* показывается:
  * название склада
  * общий объём
  * распределение по статусам

Особенности реализации:

* popup использует `MapLibre Popup`
* используется `setHTML`, а не `setText`
* данные передаются в упрощённом виде (`status_text`)
* форматирование выполняется на фронте (`split → map → join`)

---

## 9. Пустые склады

* отображаются
* `total = 0`
* `by_status = []`
* в popup отображается "нет данных"

---

## 10. Ограничения

1. Нет `by_reason`
2. Нет маршрутов
3. Агрегация on-the-fly
4. Нет кеша
5. Ограничения MapLibre:
   * не поддерживает вложенные объекты в properties
   * требует простые типы (string/number)

---

## 11. Инварианты

1. Только analytics — источник
2. Нет зависимости от OLTP
3. `current_batch_state` — факты
4. `warehouses` — география
5. Все склады отображаются
6. frontend использует `metrics.total`
7. данные для popup передаются в упрощённом виде

---

## 12. Trade-offs

1. Простота > гибкость
2. Python сборка > SQL JSON
3. Нет PostGIS
4. Один endpoint
5. Упрощение структуры данных ради совместимости с MapLibre

---

## 13. Итог

Project №3 реализует:

* чистую аналитическую карту
* строгий API без legacy
* полную независимость от OLTP
* интерактивную аналитику через popup
* читаемое представление данных пользователю

---

Архитектура Project №3 зафиксирована (V1 Final, Clean).
