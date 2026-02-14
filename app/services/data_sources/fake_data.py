# app/services/data_sources/fake_data.py
from app.models.shipment import ShipmentStatus

# =====================================================
# Fake warehouses (read-model compatible)
# =====================================================

FAKE_WAREHOUSES = [
    {
        "id": "spb-01",
        "name": "Saint Petersburg DC",
        "status": "active",
        "lat": 59.9311,
        "lon": 30.3609,
        "quantity": 1200,
    },
    {
        "id": "msk-01",
        "name": "Moscow Hub",
        "status": "active",
        "lat": 55.7558,
        "lon": 37.6173,
        "quantity": 800,
    },
    {
        "id": "hel-01",
        "name": "Helsinki Crossdock",
        "status": "active",
        "lat": 60.1699,
        "lon": 24.9384,
        "quantity": 150,
    },
    {
        "id": "kzn-01",
        "name": "Kazan Sort Center",
        "status": "active",
        "lat": 55.7903,
        "lon": 49.1347,
        "quantity": 400,
    },
    {
        "id": "ekb-01",
        "name": "Yekaterinburg Hub",
        "status": "maintenance",
        "lat": 56.8389,
        "lon": 60.6057,
        "quantity": 0,
    },
    {
        "id": "nsk-01",
        "name": "Novosibirsk DC",
        "status": "active",
        "lat": 55.0084,
        "lon": 82.9357,
        "quantity": 220,
    },
    {
        "id": "mur-01",
        "name": "Murmansk Arctic Depot",
        "status": "active",
        "lat": 68.9585,
        "lon": 33.0827,
        "quantity": 40,
    },
    {
        "id": "sochi-01",
        "name": "Sochi Resort Hub",
        "status": "closed",
        "lat": 43.5855,
        "lon": 39.7231,
        "quantity": 15,
    },
]

# =====================================================
# Fake shipments (read-model compatible!)
# =====================================================

FAKE_SHIPMENTS = [
    {
        "id": "shp-1001",
        "from_node": "spb-01",
        "to_node": "msk-01",
        "status": ShipmentStatus.in_transit,
        "volume": 10,
    },
    {
        "id": "shp-1002",
        "from_node": "msk-01",
        "to_node": "spb-01",
        "status": ShipmentStatus.planned,
        "volume": 8,
    },
    {
        "id": "shp-1003",
        "from_node": "hel-01",
        "to_node": "spb-01",
        "status": ShipmentStatus.in_transit,
        "volume": 12,
    },
    {
        "id": "shp-1004",
        "from_node": "msk-01",
        "to_node": "kzn-01",
        "status": ShipmentStatus.planned,
        "volume": 6,
    },
    {
        "id": "shp-1005",
        "from_node": "kzn-01",
        "to_node": "ekb-01",
        "status": ShipmentStatus.in_transit,
        "volume": 9,
    },
    {
        "id": "shp-1006",
        "from_node": "ekb-01",
        "to_node": "nsk-01",
        "status": ShipmentStatus.planned,
        "volume": 7,
    },
    {
        "id": "shp-1007",
        "from_node": "mur-01",
        "to_node": "msk-01",
        "status": ShipmentStatus.delivered,
        "volume": 5,
    },
    {
        "id": "shp-1008",
        "from_node": "sochi-01",
        "to_node": "msk-01",
        "status": ShipmentStatus.cancelled,
        "volume": 0,
    },
]
