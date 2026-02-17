Если нужно просто очистить current-state

cd /opt/Logistics

Внутри контейнера БД:

docker compose exec db psql -U postgres -d logistics

И там:

TRUNCATE TABLE shipments_current RESTART IDENTITY CASCADE;
TRUNCATE TABLE warehouses_current RESTART IDENTITY CASCADE;
TRUNCATE TABLE ingest_events RESTART IDENTITY CASCADE;

Это:
	•	удалит все строки
	•	сохранит структуру
	•	не потребует миграций

Если нужно полностью пересоздать БД

docker compose down -v
docker compose up -d

-v удалит volume Postgres.

Если ты на сервере напрямую

psql -U postgres -d logistics

и те же TRUNCATE.