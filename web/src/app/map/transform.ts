// /opt/Logistics/web/src/app/map/transform.ts
// Module: pure transformations from API data to GeoJSON/bounds for the map.
//
// Инварианты:
// - детерминированность: одинаковый вход → одинаковый выход
// - без сайд-эффектов (нет fetch, нет MapLibre, нет React)
// - формат координат строго [lon, lat]
// - bounds считаются по складам (точкам), чтобы камера была стабильна и предсказуема

import type { MapResponse } from "./api";

// Bounds в формате, который принимает map.fitBounds.
// null = нет складов (или нет данных), тогда fitBounds не делаем.
export type MapBounds = [[number, number], [number, number]] | null;

export function toWarehousesGeoJson(
  warehouses: MapResponse["warehouses"]
): GeoJSON.FeatureCollection<
  GeoJSON.Point,
  {
    id: string;
    warehouse_id: string;
    name: string;
    status: string;
    total: number;
    status_text: string;
  }
> {
  return {
    type: "FeatureCollection",
    features: warehouses.map((warehouse) => {
      const feature: GeoJSON.Feature<
        GeoJSON.Point,
        {
          id: string;
          warehouse_id: string;
          name: string;
          status: string;
          total: number;
          status_text: string;
        }
      > = {
        type: "Feature",
        geometry: { type: "Point", coordinates: [warehouse.lon, warehouse.lat] },
        properties: {
          id: String(warehouse.warehouse_id),
          warehouse_id: String(warehouse.warehouse_id),
          name: warehouse.name,
          status: warehouse.status,
          total: warehouse.metrics.total,
          status_text: warehouse.metrics.by_status
            .map((s) => `${s.status_id}:${s.quantity}`)
            .join(","),
        },
      };

      return feature;
    }),
  };
}

export function toRoutesGeoJson(
  routes: MapResponse["routes"]
): GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  {
    id: string;
    status: MapResponse["routes"][number]["status"];
    from: string;
    to: string;
    volume: MapResponse["routes"][number]["volume"];
  }
> {
  return {
    type: "FeatureCollection",
    features: routes.map((r) => ({
      type: "Feature",
      geometry: { type: "LineString", coordinates: r.coordinates },
      properties: { id: r.id, status: r.status, from: r.from, to: r.to, volume: r.volume },
    })),
  };
}

export function computeBounds(warehouses: MapResponse["warehouses"]): MapBounds {
  if (warehouses.length === 0) return null;

  // Инициализируем min/max первой точкой.
  let west = warehouses[0].lon;
  let east = warehouses[0].lon;
  let south = warehouses[0].lat;
  let north = warehouses[0].lat;

  // Один проход, без зависимостей от порядка.
  for (const w of warehouses) {
    if (w.lon < west) west = w.lon;
    if (w.lon > east) east = w.lon;
    if (w.lat < south) south = w.lat;
    if (w.lat > north) north = w.lat;
  }

  return [
    [west, south],
    [east, north],
  ];
}
