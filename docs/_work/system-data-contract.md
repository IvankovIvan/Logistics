# 📘 System Data Contract (V1)

---

## 1. Цель

Зафиксировать единый контракт данных системы:

- структура данных
- типы полей
- инварианты
- API контракт

Документ является источником истины для:

- backend
- frontend
- ingestion pipeline

---

## 2. Общие правила

- все даты хранятся в UTC
- все ID — целые числа (int / bigint)
- null допускается только если явно указано
- данные не изменяются задним числом (append-only)

---

## 3. Event Store Contract

Таблица:
analytics.inventory_status_events

Поля:
- batch_id: bigint
- order_id: bigint
- sku_id: bigint
- warehouse_id: bigint
- source_location_id: bigint | null
- destination_location_id: bigint | null
- status_id: int
- status_reason_id: int
- quantity: bigint
- event_time: timestamptz (UTC)
- source_system: int
- operation_id: bigint

Инварианты:
- quantity >= 0
- event_time всегда UTC
- operation_id уникален в рамках времени
- данные append-only (нет UPDATE/DELETE)

---

## 4. Snapshot Contract

Таблица:
analytics.current_batch_state

Поля:
- batch_id: bigint
- order_id: bigint
- sku_id: bigint
- warehouse_id: bigint
- status_id: int
- quantity: bigint
- source_location_id: bigint | null
- destination_location_id: bigint | null
- last_event_time: timestamptz (UTC)

Инварианты:
- содержит только актуальное состояние
- одна запись на batch_id
- quantity >= 0

---

## 5. Map API Contract

Endpoint:
/api/analytics/map

Response:

- warehouses: list
  - warehouse_id: int
  - name: string
  - lat: float
  - lon: float
  - metrics:
	  - total: int
	  - by_status:
		  - status_id: int
		  - quantity: int

- routes: list (V1 всегда пустой)

Инварианты:
- warehouses возвращаются ВСЕГДА (даже без данных)
- metrics.total >= 0
- by_status может быть пустым

---

## 6. Warehouse API Contract

Endpoint:
/api/analytics/warehouse/{id}

Response:

- warehouse_id: int
- name: string
- city: string
- warehouse_type: string
- metrics:
	- count: int
	- sum: int
	- by_status:
		- status_id: int
		- status_text: string
		- count: int
		- sum: int

Инварианты:
- count >= 0
- sum >= 0
- by_status может быть пустым

---

## 7. CSV Contract

Endpoint:
/api/analytics/warehouse/{id}/batches.csv

Формат:

batch_id,status_id,quantity,warehouse_id,last_event_time

Инварианты:
- порядок: по last_event_time DESC
- значения не null (кроме допускаемых полей)
- last_event_time в UTC

---

## 8. Справочники

status_dict:
- status_id: int
- description: string

status_reason:
- status_reason_id: int
- is_tracking_finished: bool

Инварианты:
- status_id должен существовать в status_dict

---

## 9. Гарантии системы

- API всегда соответствует контракту
- данные не ломают типы
- frontend может полагаться на структуру
- ingest не нарушает инварианты

---
