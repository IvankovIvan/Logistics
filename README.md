# Logistics

Проект для визуализации логистики: склады и маршруты на карте.  
Архитектура сразу заложена под рост — от FAKE-данных к реальной БД и ingest.

---

## Что внутри

- **Nginx** — reverse proxy  
- **FastAPI** — backend (API + бизнес-логика)  
- **Next.js + MapLibre** — frontend (карта)  
- **Docker Compose** — единый способ запуска

---

## Архитектура

Подробная схема и пояснения:  
👉 `docs/architecture.md`

Коротко:
- фронт ходит **только** в `/api/*`
- `/api/map` — единый контракт данных для карты
- сборка данных вынесена в `services/`
- приведение форматов и enum — в `domain/`

---

## Структура репозитория

```text
.
├── docker-compose.yml      # сервисы
├── nginx/                  # reverse proxy
├── app/                    # backend (FastAPI)
│   ├── routers/            # HTTP endpoints
│   ├── services/           # бизнес-логика
│   ├── domain/             # протоколы и приведение данных
│   └── models/             # pydantic-модели
├── web/                    # frontend (Next.js)
└── docs/                   # документация
```

---

## Запуск (dev)

Из корня репозитория:

```bash
docker compose up -d --build
```

Или пересобрать только backend:

```bash
docker compose up -d --build app
```

---

## Проверка работы

### Frontend
```bash
curl -i http://localhost/ | head
```

### Health backend
```bash
curl -sS http://localhost/api/health; echo
```

### Карта (основной endpoint)
```bash
curl -sS http://localhost/api/map
```

Ожидаемо:
- `/` → Next.js
- `/api/health` → `{"status":"ok"}`
- `/api/map` → `warehouses + routes`

---

## Ключевая идея проекта

- фронт **не склеивает данные**
- формат `/api/map` стабилен
- FAKE_* можно заменить на БД/ингест **без изменения фронта**
- логика разделена: `router → service → domain`

---

## Дальнейшие шаги

- заменить FAKE_* на БД
- добавить ingest
- витрину “на сейчас”
- исторические маршруты


NAT / egress-шлюз socks5://127.0.0.1:1080

ubuntu@s205:~/infra/nginx/app$ source .venv/bin/activate
(.venv) ubuntu@s205:~/infra/nginx/app$
pip install psycopg[binary]