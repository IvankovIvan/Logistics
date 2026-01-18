"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { Map, LngLatBoundsLike } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

/**
 * Контракт /api/map (единый для карты).
 * Важно: lat/lon обязательны (бэк уже отфильтровал None).
 */
type MapWarehouse = {
  id: string;
  name: string;
  status: string;
  lon: number;
  lat: number;
};

type MapRoute = {
  id: string;
  status: "planned" | "in_transit" | "delivered" | "cancelled";
  from: string;
  to: string;
  coordinates: [number, number][]; // [[lon,lat],[lon,lat],...]
};

type MapResponse = {
  warehouses: MapWarehouse[];
  routes: MapRoute[];
};

/**
 * Универсальный fetch JSON с понятной ошибкой.
 * Если API не отдаёт 200 — увидишь причину, а не "пусто".
 */
async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${url} -> ${res.status} ${res.statusText}\n${text}`);
  }
  return (await res.json()) as T;
}

export default function Page() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [37.6, 55.75],
      zoom: 4,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", async () => {
      try {
        setError(null);

        // 1) ОДИН запрос: всё для карты
        const data = await fetchJson<MapResponse>("/api/map");

        // 2) bounds — чтобы автозумить на склады
        const bounds = new maplibregl.LngLatBounds();
        for (const w of data.warehouses) bounds.extend([w.lon, w.lat]);

        // 3) GeoJSON складов
        const warehousesGeoJson: GeoJSON.FeatureCollection<
          GeoJSON.Point,
          { id: string; name: string; status: string }
        > = {
          type: "FeatureCollection",
          features: data.warehouses.map((w) => ({
            type: "Feature",
            geometry: { type: "Point", coordinates: [w.lon, w.lat] },
            properties: { id: w.id, name: w.name, status: w.status },
          })),
        };

        // 4) GeoJSON маршрутов
        const routesGeoJson: GeoJSON.FeatureCollection<
          GeoJSON.LineString,
          { id: string; status: MapRoute["status"]; from: string; to: string }
        > = {
          type: "FeatureCollection",
          features: data.routes.map((r) => ({
            type: "Feature",
            geometry: { type: "LineString", coordinates: r.coordinates },
            properties: { id: r.id, status: r.status, from: r.from, to: r.to },
          })),
        };

        // 5) Sources
        map.addSource("warehouses", { type: "geojson", data: warehousesGeoJson });
        map.addSource("routes", { type: "geojson", data: routesGeoJson });

        // 6) Слой складов
        map.addLayer({
          id: "warehouses-layer",
          type: "circle",
          source: "warehouses",
          paint: {
            "circle-radius": 6,
            "circle-color": [
              "match",
              ["get", "status"],
              "active",
              "#2563eb",
              "maintenance",
              "#f59e0b",
              "closed",
              "#6b7280",
              "#2563eb",
            ],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
          },
        });

        // 7) Слой маршрутов (линии)
        map.addLayer({
          id: "routes-line",
          type: "line",
          source: "routes",
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

        // 8) Попап по клику на маршрут
        map.on("click", "routes-line", (e) => {
          const f = e.features?.[0];
          if (!f || !f.properties) return;
          const p = f.properties as any;

          new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setText(`Shipment ${p.id} (${p.status}) ${p.from} -> ${p.to}`)
            .addTo(map);
        });

        map.on("mouseenter", "routes-line", () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", "routes-line", () => (map.getCanvas().style.cursor = ""));

        // 9) Автозум на склады
        if (!bounds.isEmpty()) {
          map.fitBounds(bounds as LngLatBoundsLike, { padding: 80 });
        }
      } catch (e) {
        console.error(e);
        setError(String(e));
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

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

      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}