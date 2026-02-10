import pytest

from datetime import datetime, timezone
from app.services.data_sources.fake import FakeDataSource
from app.services.data_sources.ingest_memory import InMemoryIngestDataSource
from app.services.ingest.rules import apply_event
from app.models.ingest import (
    WarehouseIngestEvent,
    ShipmentIngestEvent,
    WarehouseUpsertPayload,
    ShipmentUpsertPayload,
)
from app.domain.coercion import normalize_warehouse, normalize_shipment


# =====================================================
# Helpers
# =====================================================

def seed_ingest_state():
    """
    Наполняем in-memory ingest state минимально валидными данными.
    Нужно, чтобы InMemoryIngestDataSource что-то вернул.
    """

    apply_event(
        WarehouseIngestEvent(
            event_id="wh-test-1",
            event_time=datetime(2026, 2, 1, 10, 0, 0, tzinfo=timezone.utc),
            entity_type="warehouse",
            payload=WarehouseUpsertPayload(
                id="wh-1",
                name="Test WH",
                lat=55.0,
                lon=37.0,
                status="active",
                quantity=100,
            ),
        )
    )

    apply_event(
        WarehouseIngestEvent(
            event_id="wh-test-2",
            event_time=datetime(2026, 2, 1, 10, 0, 1, tzinfo=timezone.utc),
            entity_type="warehouse",
            payload=WarehouseUpsertPayload(
                id="wh-2",
                name="Test WH 2",
                lat=56.0,
                lon=38.0,
                status="active",
                quantity=50,
            ),
        )
    )

    apply_event(
        ShipmentIngestEvent(
            event_id="sh-test-1",
            event_time=datetime(2026, 2, 1, 10, 5, 1, tzinfo=timezone.utc),
            entity_type="shipment",
            payload=ShipmentUpsertPayload(
                id="sh-1",
                from_warehouse_id="wh-1",
                to_warehouse_id="wh-2",
                status="in_transit",
            ),
        )
    )


# =====================================================
# Contract tests
# =====================================================

@pytest.mark.parametrize(
    "data_source_factory",
    [
        FakeDataSource,
        InMemoryIngestDataSource,
    ],
)
def test_read_model_contract(data_source_factory):
    """
    Контракт-тест read-model.

    Гарантирует, что любой CurrentStateDataSource:
    - отдаёт warehouses, совместимые с normalize_warehouse
    - отдаёт shipments, совместимые с normalize_shipment
    """

    # Для ingest-memory нужно предварительно наполнить state
    if data_source_factory is InMemoryIngestDataSource:
        seed_ingest_state()

    data_source = data_source_factory()

    # --- warehouses ---
    warehouses = data_source.get_warehouses()
    for raw in warehouses:
        w = normalize_warehouse(raw)
        assert w.id is not None
        assert w.lat is not None
        assert w.lon is not None
        assert w.quantity is not None

    # --- map response ---
    from app.services.map_builder import build_map_response

    map_response = build_map_response(warehouses_source=warehouses, shipments_source=[])
    for w in map_response.warehouses:
        assert w.quantity is not None

    # --- shipments ---
    shipments = data_source.get_shipments()
    for raw in shipments:
        s = normalize_shipment(raw)
        assert s.id is not None
        assert s.from_node is not None
        assert s.to_node is not None
