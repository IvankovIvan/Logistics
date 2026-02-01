# app/routers/ingest.py

from datetime import datetime, timezone
from fastapi import APIRouter, status

from app.models.ingest import (
    IngestBatch,
    IngestBatchResult,
    IngestEventResult,
)
from app.services.ingest.service import ingest_events


router = APIRouter(
    prefix="/api/ingest",
    tags=["ingest"],
)

@router.post(
    "/batch",
    response_model=IngestBatchResult,
    status_code=status.HTTP_200_OK,
    summary="Batch ingest current-state events",
    description=(
        "Принимает batch ingest-событий текущего состояния.\n\n"
        "- события обрабатываются независимо\n"
        "- частичный успех является нормой\n"
        "- порядок событий не имеет значения\n"
        "- идемпотентность обеспечивается по event_id\n\n"
        "Write-side:\n"
        "- PostgreSQL current-state storage\n"
        "- синхронная обработка\n"
        "- read-side (/api/map) обновляется автоматически"
    ),
)


@router.post(
    "/batch",
    response_model=IngestBatchResult,
    status_code=status.HTTP_200_OK,
    summary="Batch ingest current-state events",
    description=(
        "Принимает batch ingest-событий текущего состояния.\n\n"
        "- события обрабатываются независимо\n"
        "- частичный успех является нормой\n"
        "- порядок событий не имеет значения\n"
        "- идемпотентность обеспечивается по event_id\n\n"
        "Write-side:\n"
        "- PostgreSQL current-state storage\n"
        "- синхронная обработка\n"
        "- read-side (/api/map) обновляется автоматически"
    ),
)
def ingest_batch(batch: IngestBatch) -> IngestBatchResult:
    """
    HTTP-адаптер write-side ingest.

    Ответственность:
    - вызвать ingest-service
    - преобразовать результат в API-контракт
    """
    service_result = ingest_events(batch.events)
    applied_ids = set(service_result["applied_event_ids"])

    results = [
        IngestEventResult(
            event_id=ev.event_id,
            status="applied" if ev.event_id in applied_ids else "duplicate",
            reason=None,
        )
        for ev in batch.events
    ]

    return IngestBatchResult(
        received_at=datetime.now(timezone.utc),
        results=results,
    )