# app/routers/analytics_ingest.py

from fastapi import APIRouter, status

from app.models.analytics.events import AnalyticsIngestRequest
from app.models.analytics.results import AnalyticsIngestResponse
from app.services.analytics_ingest.service import ingest_analytics_events


router = APIRouter(
    prefix="/api/analytics/ingest",
    tags=["analytics-ingest"],
)


@router.post(
    "/events",
    response_model=AnalyticsIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest analytics events",
    description=(
        "Append-only ingest for event sourcing layer.\n\n"
        "- события записываются в `analytics.inventory_status_events`\n"
        "- идемпотентность обеспечивается по `operation_id` + `event_time`\n"
        "- повторная отправка того же события вернёт статус `duplicate`\n"
        "- события обрабатываются независимо (частичный успех — норма)\n\n"
        "**Не пишет в snapshot** (`current_batch_state`) — "
        "snapshot обновляет только `analytics-worker`."
    ),
)
def ingest_analytics_batch(request: AnalyticsIngestRequest) -> AnalyticsIngestResponse:
    """
    HTTP-адаптер analytics write-side.

    Ответственность:
    - вызвать analytics ingest service
    - вернуть результат в API-контракт
    """
    return ingest_analytics_events(request.events)
