// web/src/app/map/sources/map.sources.ts
// Источники карты (GeoJSON sources)
//
// Ответственность модуля:
// - добавить ВСЕ источники карты
// - обновлять данные через setData
//
// Инварианты:
// - вызывается ТОЛЬКО из MapView
// - addSources → ровно один раз
// - updateSources → много раз

import type { Map, GeoJSONSource } from "maplibre-gl";
import { MAP_SOURCES } from "../constants";

import type { FeatureCollection, Point, LineString } from "geojson";

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

export type WarehousesGeoJson = FeatureCollection<
  Point,
  { id: string; name: string; status: string; quantity: number }
>;

export type RoutesGeoJson = FeatureCollection<
  LineString,
  { id: string; status: string; from: string; to: string }
>;

/* ------------------------------------------------------------------ */
/* Add sources                                                         */
/* ------------------------------------------------------------------ */

/**
 * Добавляет все источники карты.
 *
 * ВАЖНО:
 * - функция вызывается ровно один раз
 * - style УЖЕ загружен
 */
export function addMapSources(
  map: Map,
  warehouses: WarehousesGeoJson,
  routes: FeatureCollection
): void {
  map.addSource(MAP_SOURCES.WAREHOUSES, {
    type: "geojson",
    data: warehouses,
  });

  map.addSource(MAP_SOURCES.ROUTES, {
    type: "geojson",
    data: routes,
  });
}

/* ------------------------------------------------------------------ */
/* Update sources                                                      */
/* ------------------------------------------------------------------ */

/**
 * Обновляет данные источников.
 *
 * Используется при:
 * - новом poll
 * - новом batch ingest
 * - refresh данных
 */
export function updateRouteSource(
  map: Map,
  routes: FeatureCollection
): void {
  const source = map.getSource(
    MAP_SOURCES.ROUTES
  ) as GeoJSONSource | undefined;

  source?.setData(routes);
}
