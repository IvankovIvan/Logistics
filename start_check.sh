#!/bin/bash
set -e

# =========================================================
# Скрипт запуска и проверки проекта: FastAPI + Next.js + Nginx
# =========================================================
# 1️⃣ Поднимаем backend и frontend (web)
# 2️⃣ Ждём, пока они станут "healthy"
# 3️⃣ Проверяем их работу напрямую и через nginx
# 4️⃣ Выводим статус и последние логи
# =========================================================

# Цвета для удобства
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
NC="\033[0m" # без цвета

# ---------------------------------------------------------
# ШАГ 1: Поднимаем backend и frontend
# ---------------------------------------------------------
echo -e "${YELLOW}=== 1️⃣ Поднимаем backend и frontend ===${NC}"
docker compose up -d app web

# Ждём, пока контейнеры станут healthy
echo -e "${YELLOW}=== Ждём health статусов ===${NC}"
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
# ШАГ 2: Проверка backend напрямую
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 2️⃣ Проверка backend (FastAPI) ===${NC}"
docker exec -it nginx-app-1 sh -c "apk add --no-cache curl 2>/dev/null || true; curl -s http://127.0.0.1:8000/api/health || echo 'FAIL'"

# ---------------------------------------------------------
# ШАГ 3: Проверка frontend напрямую
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 3️⃣ Проверка frontend (Next.js) ===${NC}"
docker exec -it nginx-web-1 sh -c "ls -la /web/node_modules/.bin/next || echo 'NO_NEXT'; /web/node_modules/.bin/next --version || echo 'NEXT_FAIL'"

# ---------------------------------------------------------
# ШАГ 4: Проверка фронта через nginx
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 4️⃣ Проверка фронта через nginx ===${NC}"
curl -I http://127.0.0.1/ | head -n 5 || echo -e "${RED}FRONT_FAIL${NC}"

# ---------------------------------------------------------
# ШАГ 5: Проверка бэка через nginx
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 5️⃣ Проверка backend через nginx ===${NC}"
curl -I http://127.0.0.1/api/health | head -n 5 || echo -e "${RED}BACK_FAIL${NC}"

# ---------------------------------------------------------
# ШАГ 6: Проверка, что фронт реально слушает порт 3000 внутри контейнера
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 6️⃣ Проверка порта 3000 frontend ===${NC}"
docker exec -it nginx-web-1 sh -c \
"node -e \"require('http').get('http://127.0.0.1:3000',r=>{console.log('status',r.statusCode);process.exit(r.statusCode<500?0:1)}).on('error',e=>{console.error('ERR',e.message);process.exit(1)})\" || echo 'APP_LOG_FAIL'"

# ---------------------------------------------------------
# ШАГ 7: Вывод последних 50 строк логов контейнеров
# ---------------------------------------------------------
echo -e "\n${YELLOW}=== 7️⃣ Логи frontend и backend (последние 50 строк) ===${NC}"
echo "-- nginx-web-1 --"
docker logs nginx-web-1 --tail 50
echo "-- nginx-app-1 --"
docker logs nginx-app-1 --tail 50

echo -e "\n${GREEN}✅ Проверка завершена.${NC}"
