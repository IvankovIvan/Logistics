# 📘 Project №11 — Departure Metrics (V1)

---

## 1. Цель

Добавить аналитику по плановой дате отправки (planned_departure_time)
в popup склада.

Назначение:

- отслеживать просрочку отправок
- выявлять критические партии
- показывать SLA-метрики по складу

---

## 2. Источник данных

analytics.current_batch_state

Используется поле:

planned_departure_time (timestamptz | null)

---

## 3. Общая логика

Аналитика строится только по партиям:

WHERE planned_departure_time IS NOT NULL

Все расчёты выполняются на уровне склада.

---

## 4. Метрики

Расчёт выполняется по количеству строк (batch), НЕ по quantity.

### 4.1 total_with_plan

COUNT(*) WHERE planned_departure_time IS NOT NULL

---

### 4.2 overdue

planned_departure_time < NOW()

---

### 4.3 lt_1h

NOW() <= planned_departure_time < NOW() + INTERVAL '1 hour'

---

### 4.4 lt_3h

NOW() <= planned_departure_time < NOW() + INTERVAL '3 hours'

---

## 5. Проценты

Все проценты считаются относительно:

total_with_plan

Если total_with_plan = 0:

→ все значения = 0

---

## 6. API изменения

Расширяется структура popup:

metrics:

{
  "count": int,
  "sum": int,
  "by_status": [...],

  "departure_metrics": {
    "total_with_plan": int,

    "overdue": {
      "count": int,
      "percent": float
    },

    "lt_1h": {
      "count": int,
      "percent": float
    },

    "lt_3h": {
      "count": int,
      "percent": float
    }
  }
}

---

## 7. SQL подход

Расчёт выполняется:

- в одном SQL-запросе
- через CASE + COUNT
- с использованием NOW()

Без дополнительных запросов.

---

## 8. Инварианты

- snapshot — источник истины
- считаем только строки
- planned_departure_time может быть NULL
- используется время БД (NOW())
- API не зависит от структуры БД
- расчёт детерминирован

---

## 9. Ограничения

- нет учёта timezone
- нет истории изменений
- нет SLA конфигурации
- нет фильтров

---

## 10. Итог

Project №11 добавляет:

- SLA-метрики по складу
- анализ просрочек
- расширение popup API

Без изменения существующих endpoint.

---

## 11. Текущий статус реализации

### 11.1 DB

Добавлено поле:

planned_departure_time (timestamptz | null)

в таблицы:

- analytics.inventory_status_events
- analytics.current_batch_state

---

### 11.2 Ingest

Поле поддерживается:

- model (AnalyticsEvent)
- service (event params + batch insert)
- repository (fallback insert)

Поле корректно записывается в event store.

---

### 11.3 Worker

Поле поддерживается:

- SELECT из event store
- UPSERT в snapshot
- обновление при новых событиях

---

### 11.4 Rebuild

Поле поддерживается:

- latest_events
- filtered
- INSERT snapshot

Исправлен порядок колонок:
planned_departure_time и last_event_time.

---

### 11.5 Ограничения текущей реализации

- поле пока не используется в API
- метрики не реализованы
- проценты не рассчитываются
- frontend не отображает данные

---

### 11.6 Инварианты

- поле может быть NULL
- поле не участвует в idempotency
- поле не влияет на worker логику
- используется только для аналитики
