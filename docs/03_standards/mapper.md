# 🔄 Mapper Standards (обязательные правила)

## 1. Назначение

- Mapper преобразует:
  - raw dict (из repository)
  → Pydantic модель (API)

- Mapper — граница между DB и API

---

## 2. Входные данные

- Mapper принимает только:

    dict
    list[dict]

- Данные считаются "грязными"

---

## 3. Выходные данные

- Mapper возвращает:

    Pydantic модель
    list[Pydantic]

- Запрещено возвращать dict

---

## 4. Типизация

- Все поля приводятся явно:

    int(...)
    str(...)
    float(...)

- Запрещено передавать значения как есть

---

## 5. Datetime

- Обрабатывается явно:

    value.isoformat() if value else ""

---

## 6. Структура

Пример:

    def to_map_warehouse(row: dict) -> MapWarehouse:
        return MapWarehouse(
            warehouse_id=int(row["warehouse_id"]),
            name=str(row["name"]),
            lat=float(row["lat"]),
            lon=float(row["lon"]),
        )

---

## 7. Запрещено

- писать SQL
- делать HTTP
- вызывать repository
- писать бизнес-логику

---

## 8. Где используется

- Только в service
- Никогда в router

---

## 9. Инварианты

- Mapper знает:
  - структуру DB
  - структуру API

- Mapper изолирует изменения:
  - DB можно менять
  - API остаётся стабильным

---

НЕ добавляй лишнего  
НЕ меняй другие файлы  
