# Runbook

## App (backend)

### Запуск с пересборкой
Использовать после любых изменений кода, зависимостей или Dockerfile.

```bash
cd ~/infra/nginx
docker compose up -d --build app
