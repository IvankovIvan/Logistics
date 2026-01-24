# Импортируем главный класс FastAPI
# Он нужен, чтобы создать веб-приложение
from fastapi import FastAPI, HTTPException

# Создаём объект приложения
# title — это имя API (видно в документации)
app = FastAPI(title="Logistics API")




# -----------------------------
# СЛУЖЕБНЫЙ ЭНДПОИНТ
# -----------------------------

# GET /
# Используется как health-check
# Показывает, что сервис жив
@app.get("/")
def health():
    # Возвращаем Python-словарь
    # FastAPI сам превратит его в JSON
    return {"status": "ok"}

# -----------------------------
# ЛОГИСТИКА: СКЛАДЫ
# -----------------------------

# GET /warehouses
# Возвращает список складов
@app.get("/warehouses")
def get_warehouses():
    # Пока данные захардкожены (без БД)
    # Позже заменим это на запрос к базе данных
    warehouses = [
        {
            "id": "spb-01",          # уникальный ID склада
            "name": "Saint Petersburg DC",
            "status": "active"       # active / closed / maintenance
        },
        {
            "id": "msk-01",
            "name": "Moscow Hub",
            "status": "active"
        }
    ]

    # Возвращаем список складов
    return warehouses

# GET /warehouses/{warehouse_id}
# Возвращает один склад по его id
@app.get("/warehouses/{warehouse_id}")
def get_warehouse(warehouse_id: str):
    # Временно ищем в том же списке (позже будет БД)
    for w in get_warehouses():
        if w["id"] == warehouse_id:
            return w

    # Если не нашли — вернём стандартный ответ "не найдено"
    raise HTTPException(status_code=404, detail="Warehouse not found")

# -----------------------------
# ЛОГИСТИКА: ПЕРЕВОЗКИ
# -----------------------------

# GET /shipments
# Возвращает список перевозок (пока без БД)
@app.get("/shipments")
def get_shipments():
    return [
        {
            "id": "shp-1001",
            "from": "spb-01",
            "to": "msk-01",
            "status": "in_transit"   # planned / in_transit / delivered / cancelled
        },
        {
            "id": "shp-1002",
            "from": "msk-01",
            "to": "spb-01",
            "status": "planned"
        }
    ]
