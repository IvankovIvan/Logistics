// Module: screen orchestrator for the map page.
// Invariants: no SDK logic here; data/transform/render remain in their layers.

"use client";

import { useMemo, useState } from "react";

import MapView from "./MapView";
import { useMapPolling } from "./map/useMapPolling";
import { computeBounds, toRoutesGeoJson, toWarehousesGeoJson } from "./map/transform";

export default function Page() {
  const [isMapReady, setIsMapReady] = useState(false);

  const { data, error } = useMapPolling({
    enabled: isMapReady,
  });

  const warehousesGeoJson = useMemo(
    () => (data ? toWarehousesGeoJson(data.warehouses) : null),
    [data]
  );
  const routesGeoJson = useMemo(
    () => (data ? toRoutesGeoJson(data.routes) : null),
    [data]
  );
  const bounds = useMemo(() => (data ? computeBounds(data.warehouses) : null), [data]);

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      {error ? (
        <div
          style={{
            position: "absolute",
            zIndex: 10,
            top: 12,
            left: 12,
            right: 12,
            padding: 12,
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 10,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            whiteSpace: "pre-wrap",
          }}
        >
          {error}
        </div>
      ) : null}

      <MapView
        warehousesGeoJson={warehousesGeoJson}
        routesGeoJson={routesGeoJson}
        bounds={bounds}
        onReady={() => setIsMapReady(true)}
      />
    </div>
  );
}
