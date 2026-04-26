# ⚙️ Service Standards (обязательные правила)

## 1. Назначение

- Service — слой бизнес-логики
- Оркестрирует:
  - repository
  - mapper

- Service НЕ работает напрямую с HTTP

---

## 2. Что делает service

- вызывает repository
- агрегирует данные
- применяет бизнес-правила
- вызывает mapper

---

## 3. Что НЕ делает service

Запрещено:

- писать SQL
- возвращать raw dict
- работать с FastAPI (Request, Response)
- генерировать HTTPException (кроме бизнес-ошибок)

---

## 4. Входные данные

- принимает примитивы:

    int
    str
    float

- или DTO (Pydantic)

---

## 5. Выходные данные

- возвращает:

    Pydantic модели
    list[Pydantic]

- Запрещено возвращать dict

---

## 6. Работа с repository

Пример:

    rows = repository.get_warehouses(conn)

---

## 7. Работа с mapper

Пример:

    return [
        to_map_warehouse(row)
        for row in rows
    ]

---

## 8. Ошибки

- бизнес-ошибки обрабатываются в service
- HTTP ошибки — в router

---

## 9. Структура

Пример:

    def get_map_data() -> list[MapWarehouse]:
        rows = repository.get_map_data()
        return [to_map_warehouse(r) for r in rows]

---

## 10. Инварианты

- Service не знает про HTTP
- Service не знает про frontend
- Service не знает структуру БД напрямую

---

НЕ добавляй лишнего  
НЕ меняй другие файлы  
