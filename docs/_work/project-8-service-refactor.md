# /opt/Logistics/docs/_work/project-8-service-refactor.md

# 📘 Project №8 — Service Layer Refactoring & API Contracts (V1)

## 1. Цель

Привести backend к production-уровню:

- стандартизировать service layer
- зафиксировать API контракты (Pydantic)
- убрать неявную типизацию
- устранить размазанную бизнес-логику

---

## 2. Область работ

Включает:

- app/services/*
- app/routers/*
- app/models/*

Не включает:

- ingestion pipeline (Project №4)
- event store (Project №2)
- snapshot
- database schema

---

## 3. Архитектурные принципы

Сохраняются:

router → service → DB

Дополнительно:

- service = одна ответственность
- router = без логики
- models:
  - request
  - response
  - internal

---

## 4. Основные проблемы (гипотеза)

- services перегружены
- нет чёткого разделения логики
- слабая типизация psycopg
- возможны raw dict в API
- модели смешаны (API + внутренние)

---

## 5. План работ

### Step 1 — Audit services
- найти все сервисы
- определить их ответственность
- выявить нарушения архитектуры

---

### Step 2 — Classification
- разделить сервисы:
  - ingest
  - analytics
  - map
  - popup
- определить границы

---

### Step 3 — Refactor services
- разделить большие сервисы
- убрать лишнюю логику
- нормализовать SQL слой

---

### Step 4 — Models cleanup
- разделить модели:
  - request
  - response
  - internal
- убрать лишние

---

### Step 5 — API contracts
- везде response_model
- убрать dict
- привести Swagger к стандарту

---

### Step 6 — Final verification
- проверить API
- проверить Swagger
- проверить интеграцию frontend

---

## 6. Инварианты

- архитектура НЕ меняется
- ingestion НЕ трогается
- DB НЕ меняется
- каждый шаг → commit

---

## 7. Критерий успеха

- нет raw dict в API
- все endpoints имеют Pydantic
- services читаются как отдельные модули
- код предсказуем