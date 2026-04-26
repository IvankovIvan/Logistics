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
