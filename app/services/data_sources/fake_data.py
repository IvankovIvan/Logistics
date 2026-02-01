# app/services/data_sources/fake_data.py

FAKE_WAREHOUSES = [
    {
        "id": "wh-1",
        "name": "Fake Warehouse 1",
        "lat": 55.7558,
        "lon": 37.6173,
        "status": "active",
    },
    {
        "id": "wh-2",
        "name": "Fake Warehouse 2",
        "lat": 59.9311,
        "lon": 30.3609,
        "status": "active",
    },
]

FAKE_SHIPMENTS = [
    {
        "id": "sh-1",
        "from_node": "wh-1",
        "to_node": "wh-2",
        "status": "planned",
    }
]