from fastapi import FastAPI

from routers import shipments_router, warehouses_router, map_router


app = FastAPI(
    title="Logistics API",
    description="API для управления складами и перевозками",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/openapi.json",
)

@app.get(
    "/api/health",
    summary="Health-check",
    description="Проверка, что сервис запущен и отвечает.",
    tags=["service"],
)
def api_health():
    return {"status": "ok"}

@app.get(
    "/",
    summary="Health-check",
    description="Проверка, что сервис запущен и отвечает.",
    tags=["service"],
)
def health():
    return {"status": "ok"}

app.include_router(warehouses_router)
app.include_router(shipments_router)
app.include_router(map_router)
