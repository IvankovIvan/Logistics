#!/bin/bash
set -e

# =========================================================
# Скрипт полного запуска проекта:
# FastAPI (app), Next.js (web), Nginx (nginx)
# ---------------------------------------------------------
# Nginx поднимается только после healthy backend и frontend
# =========================================================

GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m"

# ---------------------------------------------------------
# ШАГ 1: Поднимаем backend и frontend
# ---------------------------------------------------------
echo -e "${YELLOW}=== 1️⃣ Поднимаем backend и frontend ===${NC}"
docker compose up -d app web

# ---------------------------------------------------------
# ШАГ 2: Ждём health статусов app и web
# ---------------------------------------------------------
for svc in app web; do
    echo "Ждём $svc..."
    for i in {1..30}; do
        status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' nginx-$svc-1)
        if [ "$status" = "healthy" ]; then
            echo -e "${GREEN}$svc is healthy${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
done

# ---------------------------------------------------------
# ШАГ 3: Поднимаем Nginx после healthy backend + frontend
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 3️⃣ Поднимаем Nginx ===${NC}"
docker compose up -d nginx

# Ждём несколько секунд, чтобы nginx стартовал
sleep 5

# ---------------------------------------------------------
# ШАГ 4: Проверяем frontend и backend напрямую
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 4️⃣ Проверка backend напрямую ===${NC}"
docker exec -it nginx-app-1 sh -c "apk add --no-cache curl 2>/dev/null || true; curl -s http://127.0.0.1:8000/api/health || echo 'FAIL'"

echo -e "\n${YELLOW}=== 5️⃣ Проверка frontend напрямую ===${NC}"
docker exec -it nginx-web-1 sh -c "ls -la /web/node_modules/.bin/next || echo 'NO_NEXT'; /web/node_modules/.bin/next --version || echo 'NEXT_FAIL'"

# ---------------------------------------------------------
# ШАГ 5: Проверка frontend и backend через Nginx
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 6️⃣ Проверка фронта через nginx ===${NC}"
curl -I http://127.0.0.1/ | head -n 5 || echo -e "${RED}FRONT_FAIL${NC}"

echo -e "\n${YELLOW}=== 7️⃣ Проверка backend через nginx ===${NC}"
curl -I http://127.0.0.1/api/health | head -n 5 || echo -e "${RED}BACK_FAIL${NC}"

# ---------------------------------------------------------
# ШАГ 6: Проверка, что фронт реально слушает порт 3000 внутри контейнера
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 8️⃣ Проверка порта 3000 frontend ===${NC}"
docker exec -it nginx-web-1 sh -c \
"node -e \"require('http').get('http://127.0.0.1:3000',r=>{console.log('status',r.statusCode);process.exit(r.statusCode<500?0:1)}).on('error',e=>{console.error('ERR',e.message);process.exit(1)})\" || echo 'APP_LOG_FAIL'"

# ---------------------------------------------------------
# ШАГ 7: Последние 50 строк логов
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 9️⃣ Логи frontend и backend (последние 50 строк) ===${NC}"
echo "-- nginx-web-1 --"
docker logs nginx-web-1 --tail 50
echo "-- nginx-app-1 --"
docker logs nginx-app-1 --tail 50

echo -e "\n${GREEN}✅ Полный запуск и проверка завершены.${NC}"
