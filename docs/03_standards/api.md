# 📐 API Standards (обязательные правила)

## 1. Общие принципы

- Все endpoints обязаны иметь `response_model`
- Запрещено возвращать `dict` напрямую
- Все ответы типизируются через Pydantic модели
- Swagger должен полностью описывать API

---

## 2. Response Model

Обязательно:

- используется `response_model=...`
- соответствует фактическому ответу
- не содержит лишних полей

---

## 3. Request Model

- все POST/PUT используют Pydantic
- запрещено принимать raw dict
- все поля валидируются

---

## 4. Ошибки

- используются HTTPException
- указывается status_code
- указывается detail

Пример:

raise HTTPException(
    status_code=404,
    detail="Not found",
)

---

## 5. Streaming (CSV)

- используется StreamingResponse
- обязательно:
  - media_type="text/csv"
  - Content-Disposition header

---

## 6. Типизация

- запрещено использовать Any без причины
- запрещено использовать object
- все данные приводятся к int / str / float

---

## 7. Разделение ответственности

- router:
  - только HTTP слой
  - без бизнес логики

- service:
  - orchestration
  - не содержит SQL

- repository:
  - содержит SQL
  - возвращает raw данные

---

## 8. Mapper Layer

- преобразует raw данные → Pydantic
- запрещено мапить данные в router

---

## 9. Инварианты

- API не зависит от DB структуры
- API не возвращает внутренние модели
- API стабилен для frontend

## 10. Project-specific constraints (обязательно)

### 10.1 DB → API типизация

- Данные из repository считаются "грязными"
- Все поля должны явно приводиться:
  - int(...)
  - str(...)
  - float(...)
- Запрещено напрямую передавать значения из БД в модели

---

### 10.2 Datetime

- Значения datetime из БД могут быть null
- Перед использованием обязательно:

    value.isoformat() if value else ""

---

### 10.3 Service vs Model

- Запрещено смешивать модели:
  - app.services.* → внутренние структуры
  - app.models.* → API контракт

- Нельзя передавать service-модель в response_model

---

### 10.4 Mapper contract

- Mapper обязан возвращать строго Pydantic модель
- Mapper принимает raw dict из repository

Тип mapper:

    def to_map_warehouse(data: dict) -> MapWarehouse

---

### 10.5 Router input

- Router не работает с raw dict
- Router принимает уже подготовленные данные (через mapper)

---

### 10.6 CSV export

- Все значения должны быть сериализованы явно
- datetime → isoformat
- null → пустая строка