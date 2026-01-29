// Module: pure transformations from API data to GeoJSON/bounds for the map.
// Invariants: deterministic output, no side effects, order-independent aggregation.

import type { MapResponse } from "./api";

export type MapBounds = [[number, number], [number, number]] | null;

export function toWarehousesGeoJson(
  warehouses: MapResponse["warehouses"]
): GeoJSON.FeatureCollection<GeoJSON.Point, { id: string; name: string; status: string }> {
  return {
    type: "FeatureCollection",
    features: warehouses.map((w) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [w.lon, w.lat] },
      properties: { id: w.id, name: w.name, status: w.status },
    })),
  };
}

export function toRoutesGeoJson(
  routes: MapResponse["routes"]
): GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  { id: string; status: MapResponse["routes"][number]["status"]; from: string; to: string }
> {
  return {
    type: "FeatureCollection",
    features: routes.map((r) => ({
      type: "Feature",
      geometry: { type: "LineString", coordinates: r.coordinates },
      properties: { id: r.id, status: r.status, from: r.from, to: r.to },
    })),
  };
}

export function computeBounds(warehouses: MapResponse["warehouses"]): MapBounds {
  if (warehouses.length === 0) return null;

  let west = warehouses[0].lon;
  let east = warehouses[0].lon;
  let south = warehouses[0].lat;
  let north = warehouses[0].lat;

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
