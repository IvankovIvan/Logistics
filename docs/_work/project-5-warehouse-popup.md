# 📘 Project №5 — Warehouse Popup & Export Architecture (V1 Draft)

---

## 1. Цель

Project №5 — расширение аналитической карты (Project №3)
путём добавления полноценного окна склада (popup).

Назначение:

* отображать детальную информацию по складу
* предоставлять агрегированную аналитику
* давать возможность выгрузки данных (CSV)
* не перегружать основной map API

---

## 2. Общая архитектура

```
frontend (map click)
        ↓
GET /api/analytics/warehouse/{warehouse_id}
        ↓
analytics DB:
    - warehouses
    - current_batch_state
    - status_dict
        ↓
response (popup data)

+ отдельно:

frontend (button click)
        ↓
GET /api/analytics/warehouse/{warehouse_id}/batches.csv
        ↓
CSV stream
```

---

## 3. Принципы

* map API НЕ расширяется
* popup = отдельный endpoint
* snapshot (`current_batch_state`) — источник истины
* backend выполняет агрегацию
* frontend отвечает только за отображение
* никакой бизнес-логики вне analytics слоя

---

## 4. Popup API

### 4.1 Endpoint

GET /api/analytics/warehouse/{warehouse_id}

---

### 4.2 Источники данных

analytics.warehouses  
analytics.cities  
analytics.warehouse_types  
analytics.current_batch_state  
analytics.status_dict  

---

### 4.3 Метаданные склада

Поля:

* warehouse_id
* name
* city
* warehouse_type

---

### 4.4 Метрики

metrics:
    count — количество партий  
    sum — сумма quantity  
    by_status — распределение  

---

### 4.5 Формат ответа

{
  "warehouse_id": 10,
  "name": "Москва",
  "city": "Москва",
  "warehouse_type": "Логистический центр",
  "metrics": {
    "count": 5,
    "sum": 120,
    "by_status": [
      {
        "status_id": 1,
        "status_text": "STORED",
        "count": 2,
        "sum": 50
      }
    ]
  }
}

---

## 5. Агрегация

### 5.1 Основной запрос

GROUP BY status_id

---

### 5.2 Метрики

* COUNT(*) — количество партий
* SUM(quantity) — суммарный объём

---

### 5.3 Total

COUNT(*) OVER ()  
SUM(quantity) OVER ()  

---

### 5.4 status_text

JOIN analytics.status_dict

---

## 6. Edge Cases

### 6.1 Склад не существует

Backend: 404 Not Found  
Frontend: "Склад не существует"

---

### 6.2 Пустой склад

count = 0  
sum = 0  
by_status = []  

---

## 7. CSV Export API

### 7.1 Endpoint

GET /api/analytics/warehouse/{warehouse_id}/batches.csv

---

### 7.2 Источник

analytics.current_batch_state

---

### 7.3 Фильтр

WHERE warehouse_id = ?

---

### 7.4 Формат CSV

batch_id,status_id,quantity,warehouse_id,last_event_time

---

### 7.5 Заголовки

Content-Type: text/csv  
Content-Disposition: attachment  

---

### 7.6 Поведение

* потоковая отдача (stream)
* без промежуточного хранения
* без дополнительной логики

---

## 8. Frontend

### 8.1 Popup

fetch /api/analytics/warehouse/{id}

---

### 8.2 Отображение

* заголовок (name + id)
* метаданные (город, тип)
* агрегаты (count + sum)
* распределение (by_status)
* кнопка CSV

---

### 8.3 CSV

window.open("/api/.../batches.csv")

---

## 9. Ограничения

1. Нет кеширования
2. Нет async export
3. Нет фильтров по партиям
4. Нет пагинации
5. Один склад за запрос

---

## 10. Инварианты

1. snapshot — источник истины
2. popup не влияет на map API
3. агрегация выполняется на backend
4. CSV соответствует snapshot
5. frontend не содержит бизнес-логики

---

## 11. Текущий этап

| Шаг | Статус |
|-----|--------|
| Архитектура | ✔ |
| Контракты API | ✔ |
| SQL | ✔ |
| Backend | ⏳ |
| Frontend | ⏳ |

---

## 12. Итог

Project №5 добавляет:

* полноценный popup склада
* агрегированную аналитику
* экспорт данных (CSV)

Без нарушения архитектуры Project №2 и Project №3.
