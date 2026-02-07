// web/src/app/map/layers/warehouses.layers.ts
// Слои складов (точки + подписи)
//
// Ответственность модуля:
// - добавить ВСЕ слои складов
// - не знать про данные, hover, камеру, события
//
// Инварианты:
// - source MAP_SOURCES.WAREHOUSES УЖЕ существует
// - функция вызывается ровно один раз

import type { Map } from "maplibre-gl";
import {
  MAP_LAYERS,
  MAP_SOURCES,
  MAP_ZOOM,
  MAP_COLORS,
} from "../constants";

/**
 * Добавляет слои складов на карту.
 *
 * Слои:
 * - circle: визуальная точка склада
 * - symbol: подпись склада (name + id)
 */
export function addWarehouseLayers(map: Map): void {
  /* ------------------------------------------------------------------ */
  /* Warehouses: points                                                  */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.WAREHOUSES_POINTS,
    type: "circle",
    source: MAP_SOURCES.WAREHOUSES,
    paint: {
      "circle-radius": 6,
      "circle-color": MAP_COLORS.WAREHOUSE_POINT,
      "circle-stroke-width": 2,
      "circle-stroke-color": MAP_COLORS.LABEL_HALO,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Warehouses: labels                                                  */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.WAREHOUSES_LABELS,
    type: "symbol",
    source: MAP_SOURCES.WAREHOUSES,
    minzoom: MAP_ZOOM.WAREHOUSE_LABELS_MIN,
    layout: {
      "text-field": ["concat", ["get", "name"], " ", ["get", "id"]],
      "text-size": 11,
      "text-anchor": "top",
      "text-offset": [0, 1.1],
      "text-allow-overlap": false,
      "text-ignore-placement": false,
    },
    paint: {
      "text-color": MAP_COLORS.WAREHOUSE_LABEL,
      "text-halo-color": MAP_COLORS.LABEL_HALO,
      "text-halo-width": 1,
    },
  });
}