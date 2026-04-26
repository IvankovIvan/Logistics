# 🚀 Logistics Project

## 1. Что это

Система аналитики логистики:

- ingest событий (MS SQL → Postgres)
- snapshot модель (current state)
- API (FastAPI)
- карта (Next.js)

---

## 2. Архитектура

Основной принцип:

    events → processing → snapshot → API → frontend

Подробнее:

- docs/00_system/SYSTEM_ARCHITECTURE.md

---

## 3. Структура проекта

    app/
      routers/        → HTTP слой
      services/       → бизнес-логика
      repositories/   → SQL
      models/         → API контракты

    docs/
      00_system/      → архитектура
      01_rules/       → правила работы
      02_projects/    → финальные проекты
      03_standards/   → стандарты кода
      05_audit/       → проверки

---

## 4. Как работать

Обязательный workflow:

    Step → Code → Audit → DoD → Commit

Подробно:

- docs/01_rules/MASTER_FILE.md
- docs/01_rules/definition_of_done.md

---

## 5. Стандарты

Код пишется строго по:

- docs/03_standards/api.md
- docs/03_standards/repository.md
- docs/03_standards/mapper.md
- docs/03_standards/service.md

---

## 6. Проверка

Перед коммитом:

- docs/05_audit/code_audit.md

---

## 7. API

Основные endpoints:

- GET /api/analytics/map
- GET /api/analytics/warehouse/{id}
- GET /api/analytics/warehouse/{id}/batches.csv
- POST /api/analytics/ingest/events

Swagger:

    /docs

---

## 8. Frontend

- Next.js
- карта + popup складов
- polling данных

---

## 9. Инварианты

- API не зависит от DB
- SQL только в repository
- mapper изолирует DB → API
- frontend зависит только от API

---

## 10. Быстрый старт

    docker compose up --build

Backend:

    http://localhost:8000/docs