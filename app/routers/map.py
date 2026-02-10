# app/routers/map.py
from __future__ import annotations

from fastapi import APIRouter

from models import MapResponse
from app.services.map_builder import build_map_response

"""
HTTP-роутер /api/map

Назначение файла:
- принять HTTP-запрос от фронта
- вызвать сервисный слой сборки витрины
- вернуть готовый MapResponse

АРХИТЕКТУРНЫЕ ПРИНЦИПЫ:
- роутер МАКСИМАЛЬНО тонкий
- НЕТ бизнес-логики
- НЕТ выбора источников данных
- НЕТ FAKE / БД / ingest упоминаний

Почему так:
- /api/map — стабильный контракт для фронта
- источник данных может меняться без правок API
- вся логика сосредоточена в services/map_builder.py
"""

router = APIRouter(
    prefix="/api/map",
    tags=["map"],
)


@router.get(
    "",
    response_model=MapResponse,
    summary="Данные для карты (current state)",
    description=(
        "Единый endpoint для экрана карты.\n\n"
        "Особенности:\n"
        "- экран «на сейчас» (current-state, без истории)\n"
        "- фронт делает ОДИН запрос\n"
        "- фронт НЕ склеивает данные\n"
        "- формат стабилен\n\n"
        "Источник данных выбирается внутри сервисного слоя "
        "(FAKE / ingest / БД) без изменения API."
    ),
)
def get_map() -> MapResponse:
    """
    Endpoint карты.

    Здесь происходит ТОЛЬКО:
    - вызов build_map_response()
    - возврат результата клиенту

    ВАЖНО:
    - роутер НЕ знает, откуда берутся данные
    - роутер НЕ передаёт источники данных явно
    - выбор источника — ответственность сервисного слоя
    """

    return build_map_response()
