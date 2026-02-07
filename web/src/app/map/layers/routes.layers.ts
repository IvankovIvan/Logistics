// file: web/src/app/map/layers/routes.layers.ts
// Слои маршрутов (линии, hover, подписи)
//
// Ответственность модуля:
// - добавить ВСЕ слои маршрутов
// - визуализировать агрегации (count, direction, status)
//
// Инварианты:
// - source "routes" УЖЕ существует
// - НИКАКОЙ логики hover или popup
// - только addLayer

import type { Map } from "maplibre-gl";
import {
  MAP_LAYERS,
  MAP_SOURCES,
  MAP_ZOOM,
  MAP_COLORS,
  ROUTE_OFFSETS,
} from "../constants";

/**
 * Добавляет все слои маршрутов:
 * - forward / backward линии
 * - hover-линии (пустые фильтры)
 * - подписи (count)
 *
 * ВАЖНО:
 * - функция идемпотентна по дизайну (вызывается один раз)
 * - порядок addLayer важен (hover поверх обычных)
 */
export function addRouteLayers(map: Map): void {
  /* ------------------------------------------------------------------ */
  /* Forward routes                                                      */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTES_MIN,
    filter: ["==", ["get", "direction"], "forward"],
    paint: {
      "line-width": [
        "interpolate",
        ["linear"],
        ["get", "count"],
        1, 2,
        3, 3,
        6, 4,
      ],
      "line-color": MAP_COLORS.ROUTE_MAIN,
      "line-offset": ROUTE_OFFSETS.FORWARD,
      "line-opacity": 0.75,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Backward routes                                                     */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTES_MIN,
    filter: ["==", ["get", "direction"], "backward"],
    paint: {
      "line-width": [
        "interpolate",
        ["linear"],
        ["get", "count"],
        1, 2,
        3, 3,
        6, 4,
      ],
      "line-color": MAP_COLORS.ROUTE_MAIN,
      "line-offset": ROUTE_OFFSETS.BACKWARD,
      "line-opacity": 0.75,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Hover layers (initially empty)                                      */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD_HOVER,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "label"], ""], // пусто по умолчанию
    paint: {
      "line-width": 3,
      "line-color": MAP_COLORS.ROUTE_HOVER,
      "line-offset": ROUTE_OFFSETS.FORWARD,
      "line-opacity": 0.9,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD_HOVER,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "label"], ""],
    paint: {
      "line-width": 3,
      "line-color": MAP_COLORS.ROUTE_HOVER,
      "line-offset": ROUTE_OFFSETS.BACKWARD,
      "line-opacity": 0.9,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Labels                                                             */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_LABELS,
    type: "symbol",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTE_LABELS_MIN,
    layout: {
      "symbol-placement": "line",
      "text-field": ["get", "label"],
      "text-size": 11,
      "text-allow-overlap": false,
      "text-ignore-placement": false,
      "text-rotation-alignment": "map",
      "text-keep-upright": true,
    },
    paint: {
      "text-color": MAP_COLORS.LABEL_TEXT,
      "text-halo-color": MAP_COLORS.LABEL_HALO,
      "text-halo-width": 1,
    },
  });
}