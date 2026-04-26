# 📘 Project №9 — Frontend Architecture Refactor (V1)

---

## 1. Цель

Привести frontend (Next.js) к production-уровню:

- стандартизировать API слой
- устранить разрозненные fetch вызовы
- ввести строгую типизацию данных
- подготовить архитектуру к масштабированию

---

## 2. Область работ

Включает:

- web/src/api/*
- web/src/app/map/*
- web/src/app/*
- frontend модели (типизация)

Не включает:

- backend API
- database
- ingestion pipeline
- analytics layer

---

## 3. Архитектурные принципы

Целевая схема:

frontend component  
→ facade  
→ api layer  
→ backend  

---

Правила:

- fetch НЕ используется напрямую вне api слоя
- facade НЕ делает HTTP вызовы
- все API вызовы централизованы
- типизация обязательна

---

## 4. Текущий state (Audit)

### Map

- используется: да
- API: /api/analytics/map
- вызов: fetchJson (частично централизован)

---

### Warehouse popup

- используется: да
- API: /api/analytics/warehouse/{id}
- вызов: через api layer

---

### CSV export

- используется: да
- API: /api/analytics/warehouse/{id}/batches.csv
- вызов: fetch + blob через api layer

---

### Общие проблемы

- нет единого API слоя
- типизация частично отсутствует
- используется inline `as {...}`
- facade смешивает ответственность
- CSV интеграция требует финальной верификации

---

## 5. План работ

### Step 1 — Centralized API layer
- создать web/src/api
- вынести все fetch вызовы

---

### Step 2 — Models typing
- описать frontend модели
- убрать `as {}`

---

### Step 3 — Facade cleanup
- facade только orchestration
- убрать HTTP

---

### Step 4 — CSV integration
- нормализовать скачивание
- добавить обработку ошибок

---

### Step 5 — Final verification
- проверить map
- проверить popup
- проверить CSV
- проверить типизацию

---

## 6. Инварианты

- backend НЕ меняется
- API endpoints НЕ меняются
- логика карты НЕ меняется
- каждый шаг → commit

---

## 7. Критерий успеха

- нет fetch вне api слоя
- нет `as {...}`
- facade не содержит HTTP логики
- frontend типизирован
- код читается и масштабируется

---

## Step 2 — Frontend models typing

Цель:
- убрать inline типизацию
- ввести строгие модели данных
- синхронизировать frontend с backend контрактами

Проблема:
- используется `as {...}`
- нет централизованных моделей
- высокая вероятность ошибок

Решение:
- создаётся слой web/src/models
- frontend использует типы вместо кастов

Результат:
- строгая типизация
- предсказуемость API

---

## Step 3 — Facade cleanup

Цель:
- упростить facade
- убрать HTTP и лишнюю логику
- оставить только orchestration

Проблема:
- facade перегружен
- смешивает API и бизнес-логику

Решение:
- facade вызывает API слой
- facade не знает про fetch

Результат:
- читаемый код
- понятные границы

---

## Step 4 — CSV integration

Цель:
- нормализовать скачивание CSV
- убрать window.open
- добавить контроль и обработку ошибок

Проблема:
- CSV скачивается напрямую через window.open
- нет обработки ошибок
- нет интеграции в API слой

Решение:
- реализовать download через fetch + blob
- добавить функцию в API слой

Результат:
- контролируемое скачивание
- единая архитектура