# Runbook

## Запуск

```bash
cd ~/infra/nginx
docker compose up -d --build
```

Если менялся только backend:

```bash
docker compose up -d --build app
```

## Статус сервисов

```bash
docker compose ps
```

Ожидаем: `app` и `web` → `(healthy)`.

## Логи

```bash
docker compose logs -f app
docker compose logs -f web
docker compose logs -f nginx
```

## Smoke-check

### backend health

```bash
curl -sS http://127.0.0.1/api/health; echo
```

### map endpoint

```bash
curl -sS http://127.0.0.1/api/map | head -c 300; echo
```

### фронт

```bash
curl -i http://127.0.0.1/ | head
```

## Типовые проблемы

### `502 Bad Gateway` на `/api/*`

1) Логи app:

```bash
docker compose logs --tail 200 app
```

2) Проверка health:

```bash
docker compose ps
```

3) Пересборка app:

```bash
docker compose up -d --build app
```

### В контейнере нет curl/jq/wget

Нормально для slim-образов. Проверяй через Python:

```bash
docker exec -it nginx-app-1 sh -lc "python - <<'PY'
import json, urllib.request
url = 'http://127.0.0.1:8000/api/map'
with urllib.request.urlopen(url, timeout=5) as r:
    data = r.read().decode('utf-8')
obj = json.loads(data)
print('keys:', list(obj.keys()))
print('warehouses:', len(obj.get('warehouses', [])))
print('routes:', len(obj.get('routes', [])))
PY"
```
