# /opt/Logistics/docs/_work/project-7-code-structure.md

# 📘 Project №7 — Code Structure Architecture (V1 Draft)

---

## 1. Цель

Project №7 — формализация структуры кодовой базы проекта.

Назначение:

- описать структуру проекта на уровне файлов
- определить ответственность каждого файла
- зафиксировать связи между компонентами
- упростить навигацию по проекту

---

## 2. Общая идея

Проект представляет собой документацию кодовой базы
в виде структурированной карты.

Описание выполняется:

- по слоям (router / service / worker / db)
- с указанием файлов
- с кратким описанием их ответственности

Документ НЕ изменяет архитектуру,
а только фиксирует текущее состояние системы.

---

## 3. Область анализа

В анализ включаются:

- backend (app)
- database (db)
- ingestion pipeline
- workers
- frontend (если присутствует)
- docker и конфигурация
- документация проекта

---

## 4. Ограничения

1. не выполняется рефакторинг
2. не предлагаются улучшения
3. не анализируется качество кода
4. описание краткое (1–2 строки на файл)
5. архитектура не изменяется

## 5. Структура проекта

### 5.1 Backend

app/

Содержит:
- routers — HTTP слой
- services — бизнес-логика
- workers — фоновая обработка
- models — структуры данных (DTO, API контракты)

---

### 5.2 Data layer

db/

Содержит:
- init.sql
- analytics схемы
- миграции

---

### 5.3 Frontend

web/

Содержит:
- Next.js приложение
- карта (MapLibre)
- UI компоненты
- API взаимодействие

---

### 5.4 Infrastructure

Содержит:
- docker-compose.yml
- nginx/
- Dockerfile

---

### 5.5 Documentation

docs/

Содержит:
- архитектурные документы
- описание проектов
- правила разработки

---

## 6. Игнорируемые и лишние элементы

Следующие элементы не используются в текущей архитектуре
и подлежат удалению в рамках cleanup (Project №6):

- app/domain/ — пустая директория
- html/ — legacy или тестовый код
- .pytest_cache/ — служебная папка тестов
- PySocks-1.7.1-py3-none-any.whl — лишний файл в репозитории
- test.txt — временный файл
- vsCode_ssh.txt — локальный файл
- _files.txt — временный файл

Важно:
- не удалять автоматически
- используется только как список для cleanup

## 7. Backend (app)

app/ — основной backend проекта

Назначение:
- содержит API
- содержит бизнес-логику
- реализует ingestion и аналитику
- взаимодействует с базой данных

Структура:

- routers — HTTP слой (endpoint'ы)
- services — бизнес-логика и работа с БД
- workers — фоновая обработка (batch processing)
- models — структуры данных (DTO, API контракты)
- tests — тесты (если используются)

## 7.1 Routers (HTTP слой)

app/routers — слой API

Назначение:
- принимает HTTP запросы
- валидирует входные данные (через Pydantic)
- вызывает сервисы
- возвращает response

Файлы:

### analytics_map.py
- endpoint /api/analytics/map
- возвращает агрегированные данные для карты

### analytics_ingest.py
- endpoint /api/analytics/ingest/events
- принимает batch событий для загрузки в систему

## 7.2 Services (бизнес-логика)

app/services — основной слой бизнес-логики

Назначение:
- содержит обработку данных
- выполняет SQL-запросы
- реализует ingest pipeline
- формирует ответы для API

---

### analytics_map_builder.py

- строит агрегированные данные для карты
- объединяет snapshot и справочники
- формирует response для /api/analytics/map

---

### analytics_ingest/

#### connection.py
- управление подключением к Postgres

#### queries.py
- SQL-запросы для ingest pipeline

#### service.py
- основной сервис ingest
- выполняет batch insert
- обрабатывает idempotency и fallback

---

### analytics_rebuild/

#### service.py
- выполняет полный rebuild snapshot

#### consistency_check.py
- проверяет корректность snapshot после rebuild

## 7.3 Workers (фоновые процессы)

app/workers — слой фоновой обработки данных

Назначение:
- выполняет batch обработку
- обновляет snapshot
- реализует ingestion pipeline

---

### analytics_worker.py

- основной worker аналитики
- читает события из event store
- обновляет current_batch_state
- поддерживает консистентность snapshot

---

### mssql_extractor/

#### main.py
- основной цикл extractor
- управляет fetch → send → retry

#### mssql.py
- получение данных из MS SQL

#### api.py
- отправка batch в ingest API

#### postgres.py
- работа с ingest_cursor

#### config.py
- конфигурация extractor (env переменные)

#### dlq.py
- обработка и сохранение ошибок (Dead Letter Queue)

## 7.4 Models (структуры данных)

app/models — слой описания данных

Назначение:
- определяет структуры данных (Pydantic модели)
- используется для API (request / response)
- используется внутри сервисов и worker'ов
- обеспечивает валидацию и сериализацию

---

### map_response.py
- модель ответа для карты (/api/analytics/map)

### map_warehouse.py
- модель склада для карты

### map_route.py
- модель маршрута для карты

---

### warehouse.py
- доменная модель склада

### shipment.py
- доменная модель перемещения

---

### analytics/

#### events.py
- модели событий для ingest pipeline

#### results.py
- модели результатов обработки

#### warehouse_metadata.py
- модели метаданных склада

---

### ingest/

#### events.py
- модели входящих событий (request)

#### results.py
- модели ответов ingest API

---

### enums/

#### shipment_status.py
- статусы перемещений

#### warehouse_status.py
- статусы складов

---

## 7.5 Database (db)

db/ — слой базы данных

Назначение:
- хранение структуры базы данных
- инициализация схем и таблиц
- хранение SQL-скриптов

---

### init.sql
- базовая инициализация БД

---

### analytics/

#### 01_init.sql
- создание аналитических таблиц
- event store и snapshot

---

### readme.md
- описание структуры базы данных

---