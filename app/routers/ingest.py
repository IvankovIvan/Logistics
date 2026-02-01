# app/routers/ingest.py
from fastapi import APIRouter, status

from app.models.ingest import (
    IngestBatch,
    IngestBatchResult,
)
from app.services.ingest.processor import process_ingest_batch


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
        "На текущем этапе:\n"
        "- используется in-memory обработка\n"
        "- без БД и без сохранения состояния между рестартами"
    ),
)
def ingest_batch(batch: IngestBatch) -> IngestBatchResult:
    """
    Batch ingest endpoint (write-side).

    Ответственность:
    - принять HTTP-запрос
    - передать batch в ingest processor
    - вернуть результат обработки

    ⚠️ Бизнес-логика, идемпотентность и правила
    находятся в services.ingest.processor / rules.
    """
    return process_ingest_batch(batch)