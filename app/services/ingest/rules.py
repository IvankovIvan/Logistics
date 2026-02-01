# app/services/ingest/rules.py
from models.ingest import IngestEvent


def apply_event(event: IngestEvent) -> None:
    """
    Применяет одно ingest-событие.

    ⚠️ Заглушка:
    - сейчас ничего не делает
    - просто подтверждает, что событие допустимо

    Позже здесь появится:
    - stale-event logic (event_time)
    - проверка ссылок
    - запись в current-state DB
    """

    # На этом этапе любое корректное событие допустимо
    return None