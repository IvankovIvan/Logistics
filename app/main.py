# app/main.py
from fastapi import FastAPI

from routers import (
    analytics_ingest_router,
    analytics_map_router,
)

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

# ⬇️ ВАЖНО:
# map_router, ingest_router, analytics_ingest_router и analytics_map_router
# УЖЕ имеют prefix="/api", поэтому не нужно его указывать здесь.
app.include_router(analytics_ingest_router)
app.include_router(analytics_map_router)