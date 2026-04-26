# 📘 Project №10 — Query Layer / Repository Architecture (V1)

---

## 1. Цель

Привести backend к production-архитектуре уровня:

- разделить SQL и бизнес-логику
- ввести слой доступа к данным (repository / query layer)
- упростить service слой
- подготовить систему к оптимизации и масштабированию

---

## 2. Область работ

Включает:

- app/services/*
- app/services/analytics/*
- app/services/analytics_ingest/*
- app/services/analytics_rebuild/*
- новый слой repositories

Не включает:

- database schema
- ingestion pipeline (логика)
- API endpoints (контракты)
- frontend

---

## 3. Архитектурные принципы

Текущая схема:

router  
→ service  
→ SQL  

---

Целевая схема:

router  
→ service  
→ repository (query layer)  
→ DB  

---

Правила:

- service НЕ содержит SQL
- repository содержит только работу с БД
- repository НЕ содержит бизнес-логики
- SQL централизован
- service = orchestration

---

## 4. Текущий state (Audit)

### Проблемы

- SQL размазан по сервисам
- смешение ответственности
- сложность чтения
- невозможность переиспользования SQL
- сложно тестировать

---

### Примеры

analytics_map_builder:
- SQL + агрегация + маппинг в одном месте

analytics_ingest/service:
- SQL builder + бизнес-логика + fallback

analytics_rebuild:
- SQL rebuild + orchestration

---

## 5. План работ

### Step 1 — Identify query boundaries
- найти SQL в сервисах
- определить группы запросов

---

### Step 2 — Create repository layer
- создать app/repositories/
- определить структуру

---

### Step 3 — Extract queries
- перенести SQL из service в repository

---

### Step 4 — Refactor services
- убрать SQL из service
- оставить orchestration

---

### Step 5 — Final verification
- проверить работу API
- проверить ingest
- проверить rebuild

---

## 6. Инварианты

- DB НЕ меняется
- ingestion логика НЕ меняется
- API НЕ меняется
- каждый шаг → commit

---

## 7. Критерий успеха

- нет SQL в service
- repository слой выделен
- service читается как бизнес-логика
- код легко расширяется

---

## Step 2 — Repository layer

Цель:
- создать слой доступа к данным
- отделить SQL от service

Решение:
- вводится папка app/repositories
- каждый домен получает свой repository

Структура:

app/repositories/
	map_repository.py
	warehouse_repository.py
	ingest_repository.py
	rebuild_repository.py

Результат:
- SQL централизован
- service упрощается

---

## Step 3 — Warehouse repository

Цель:
- вынести SQL warehouse домена в repository
- разделить metadata, metrics и batches

Решение:
- создаётся warehouse_repository
- каждая функция = отдельный SQL

Результат:
- service очищен от SQL
- код становится читаемым

---

## Step 4 — Rebuild repository

Цель:
- вынести rebuild SQL в repository слой
- отделить процедуру восстановления snapshot от orchestration

Проблема:
- rebuild содержит сложный SQL прямо в service
- сложно читать и поддерживать

Решение:
- SQL переносится в rebuild_repository
- service управляет только транзакцией и вызовами

Результат:
- чистая архитектура
- понятный rebuild pipeline

---

## Step 5 — Ingest repository

Цель:
- вынести SQL операций ingest в repository
- сохранить сложную бизнес-логику в service

Проблема:
- ingest содержит SQL + retry + fallback + batch logic

Решение:
- SQL операции переносятся в repository
- orchestration остаётся в service

Результат:
- читаемый ingest pipeline
- безопасная архитектура