"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

type Warehouse = {
  id: string;
  name: string;
  status: string;
  lat?: number | null;
  lon?: number | null;
};

type Shipment = {
  id: string;
  from: string;
  to: string;
  status: "planned" | "in_transit" | "delivered" | "cancelled";
};

function fetchJson<T>(url: string): Promise<T> {
  return fetch(url, { cache: "no-store" }).then(async (res) => {
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`${url} → ${res.status} ${res.statusText} ${text}`);
    }
    return res.json() as Promise<T>;
  });
}

/**
 * Карта:
 * - точки складов
 * - маршруты перевозок (planned + in_transit)
 */
export default function Map() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      // Phase 1: держим стиль локальным и единым с MapView для консистентности.
      style: "/map/base-style.json",
      center: [30.36, 59.93],
      zoom: 4,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    Promise.all([
      fetchJson<Warehouse[]>("/api/warehouses"),
      fetchJson<Shipment[]>("/api/shipments"),
    ])
      .then(([warehouses, shipments]) => {
        // warehouse_id -> [lon, lat]
        const coords: Record<string, [number, number]> = {};

        // --- Точки складов ---
        for (const w of warehouses) {
          if (typeof w.lat !== "number" || typeof w.lon !== "number") continue;

          coords[w.id] = [w.lon, w.lat];

          const el = document.createElement("div");
          el.style.width = "12px";
          el.style.height = "12px";
          el.style.borderRadius = "999px";
          el.style.background = w.status === "active" ? "#22c55e" : "#f59e0b";
          el.style.boxShadow = "0 0 0 2px rgba(255,255,255,0.9)";

          new maplibregl.Marker({ element: el })
            .setLngLat([w.lon, w.lat])
            .setPopup(new maplibregl.Popup().setText(`${w.name} (${w.id})`))
            .addTo(map);
        }

        // --- Линии маршрутов ---
        const features: GeoJSON.Feature<GeoJSON.LineString, { id: string; status: string }>[] = [];

        for (const sh of shipments) {
          const from = coords[sh.from];
          const to = coords[sh.to];
          if (!from || !to) continue;

          // рисуем только активные
          if (sh.status !== "planned" && sh.status !== "in_transit") continue;

          features.push({
            type: "Feature",
            geometry: { type: "LineString", coordinates: [from, to] },
            properties: { id: sh.id, status: sh.status },
          });
        }

        const geojson: GeoJSON.FeatureCollection<GeoJSON.LineString, { id: string; status: string }> = {
          type: "FeatureCollection",
          features,
        };

        // Важно: добавляем слой только после load
        map.on("load", () => {
          map.addSource("shipments-lines", {
            type: "geojson",
            data: geojson,
          });

          map.addLayer({
            id: "shipments-lines-layer",
            type: "line",
            source: "shipments-lines",
            paint: {
              "line-width": 3,
              "line-opacity": 0.9,
              "line-color": [
                "match",
                ["get", "status"],
                "in_transit",
                "#16a34a",
                "planned",
                "#f59e0b",
                "#6b7280",
              ],
            },
          });

          // Popup по клику на линию
          map.on("click", "shipments-lines-layer", (e) => {
            const f = e.features?.[0];
            if (!f) return;

            // properties приходят как any (MapLibre), поэтому приводим аккуратно
            const props = (f.properties ?? {}) as any;
            new maplibregl.Popup()
              .setLngLat(e.lngLat)
              .setText(`Shipment ${props.id} (${props.status})`)
              .addTo(map);
          });

          map.on("mouseenter", "shipments-lines-layer", () => {
            map.getCanvas().style.cursor = "pointer";
          });
          map.on("mouseleave", "shipments-lines-layer", () => {
            map.getCanvas().style.cursor = "";
          });
        });
      })
      .catch((err) => {
        console.error("Map load failed:", err);
        alert(String(err));
      });

    return () => {
      map.remove();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: 520,
        borderRadius: 12,
        overflow: "hidden",
        border: "1px solid #e5e7eb",
      }}
    />
  );
}
