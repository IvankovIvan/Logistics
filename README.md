# Logistics

Docker-compose-based infrastructure with:
- Nginx as reverse proxy
- FastAPI backend
- Next.js frontend

## Project structure

- `docker-compose.yml` — services wiring
- `nginx/` — nginx reverse proxy configuration
- `app/` — backend (FastAPI)
- `web/` — frontend (Next.js)
- `html/` — static assets
- `test.txt`, `vsCode_ssh.txt` — notes / test files

## Run (dev)

From repo root:

```bash
docker-compose up --build
```

Services:
- nginx → http://localhost
- backend (FastAPI) → internal :8000
- frontend (Next.js) → internal :3000

## Verify

Check frontend:
```bash
curl -i http://localhost/ | head
```

Check backend OpenAPI:
```bash
curl -i http://localhost/openapi.json | head
```

Check API routing:
```bash
curl -i http://localhost/api/ | head
```

Expected:
- `/` → frontend (Next.js)
- `/openapi.json` → FastAPI schema
- `/api/*` → FastAPI routes
