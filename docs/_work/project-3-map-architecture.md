# /opt/Logistics/docs/_work/project-3-map-architecture.md
# 📘 Project №3 — Analytics Map Architecture (V1 Final)

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

* `warehouse_id` — стабильный идентификатор (совпадает с OLTP)
* `name` — название склада
* `city_id` — ссылка на справочник городов
* `warehouse_type_id` — тип склада
* `lat`, `lon` — координаты (WGS84, без PostGIS)
* `created_at`, `updated_at` — технические поля

Особенности:

* не используется PostGIS
* хранится только `lat/lon`
* полностью независима от OLTP
* используется как единственный источник географии

---

### 3.3 Справочники

```
analytics.cities
analytics.warehouse_types
```

Назначение:

* нормализация данных
* исключение дублирования
* основа для фильтрации и отображения

---

## 4. Логика агрегации

Агрегация выполняется на лету:

```
GROUP BY warehouse_id, status_id
```

Источник:

```
analytics.current_batch_state
```

Результат:

* `total_quantity` — сумма по складу и статусу
* `warehouse_total_quantity` — общий объём по складу

⚠️ В V1:
* `by_reason` отсутствует

---

## 5. Объединение данных

Агрегация объединяется с географией:

```
analytics.warehouses
LEFT JOIN aggregation
ON warehouse_id
```

Особенности:

* используются ВСЕ склады
* склады без данных получают `total = 0`
* реализовано на уровне Python (map_builder)

---

## 6. API

Endpoint:

```
GET /api/analytics/map
```

Особенности:

* новый endpoint (старый /api/map не изменяется)
* один запрос
* полностью основан на analytics

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

      "quantity": 120,

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

Особенности:

* `quantity` = `metrics.total`
* используется фронтом для визуализации (радиус)
* добавлено для backward compatibility

---

## 8. Визуализация

Карта отображает:

* точки складов
* агрегированные метрики

Слои:

* общий объём (`total`)
* по статусам (`by_status`)

⚠️ В V1:
* используется `quantity` для radius (наследие Project №1)

---

## 9. Пустые склады

Склады без активных партий:

* отображаются
* имеют `total = 0`
* имеют `quantity = 0`
* `by_status = []`

---

## 10. Ограничения

1. Нет `by_reason` (будет в V2)
2. Нет маршрутов (будут позже)
3. Агрегация выполняется на лету
4. Нет кеша
5. Есть временная зависимость от старого поля `quantity`

---

## 11. Инварианты

1. Только analytics — источник данных
2. Нет зависимости от OLTP
3. `current_batch_state` — факты
4. `warehouses` — география
5. Все склады отображаются
6. `quantity = metrics.total`

---

## 12. Trade-offs

1. Простота > гибкость (V1)
2. Python сборка > SQL JSON
3. Нет PostGIS
4. Один endpoint
5. Временный слой совместимости (quantity)

---

## 13. Итог

Project №3 реализует:

* полностью независимую карту
* агрегированные метрики
* рабочий production pipeline
* совместимость со старым фронтом

---

Архитектура Project №3 зафиксирована (V1 Final).
