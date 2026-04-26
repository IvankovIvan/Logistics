Problem:
Add shipment volume support in ingest (payload model, UPSERT SQL, and service parameters) while keeping ingest/postgres layer separation intact.

Approach:
Update ShipmentUpsertPayload to require volume, extend UPSERT_SHIPMENT in ingest/queries.py, and pass volume in ingest/service.py. Keep postgres read-side queries unchanged and confirm outputs.

Workplan:
- [ ] Add volume field to ShipmentUpsertPayload (events.py)
- [ ] Update UPSERT_SHIPMENT SQL with volume column/value/update (ingest/queries.py)
- [ ] Pass volume parameter in ingest service UPSERT_SHIPMENT
- [ ] Verify postgres/queries.py has no UPSERT_SHIPMENT and show requested listings

Notes:
- Preserve stale semantics in UPSERT_SHIPMENT.
- Avoid any refactors or layer changes.
