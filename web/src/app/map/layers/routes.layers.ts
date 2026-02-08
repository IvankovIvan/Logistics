// web/src/app/map/layers/routes.layers.ts
//
// Слои маршрутов.
//
// Ответственность:
// - отрисовка линий
// - отрисовка стрелок
// - подготовка hover-слоёв
//
// ВАЖНО:
// - source "routes" уже существует
// - direction приходит из transform
// - НИКАКОЙ логики hover здесь нет

import type { Map } from "maplibre-gl";
import {
  MAP_LAYERS,
  MAP_SOURCES,
  MAP_ZOOM,
  MAP_COLORS,
} from "../constants";

export function addRouteLayers(map: Map): void {
  /* ------------------------------------------------------------------ */
  /* Lines                                                              */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTES_MIN,
    filter: ["==", ["get", "direction"], "forward"],
    paint: {
      "line-width": 2,
      "line-color": MAP_COLORS.ROUTE_MAIN,
      "line-opacity": 0.75,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTES_MIN,
    filter: ["==", ["get", "direction"], "backward"],
    paint: {
      "line-width": 2,
      "line-color": MAP_COLORS.ROUTE_MAIN,
      "line-opacity": 0.75,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Arrows                                                             */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD_ARROWS,
    type: "symbol",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTES_MIN,
    filter: ["==", ["get", "direction"], "forward"],
    layout: {
      "symbol-placement": "line",
      "text-field": "▶",
      "symbol-spacing": 80,
      "text-size": 12,
      "text-rotation-alignment": "map",
      "text-keep-upright": true,
    },
    paint: {
      "text-color": MAP_COLORS.ROUTE_MAIN,
      "text-halo-color": MAP_COLORS.LABEL_HALO,
      "text-halo-width": 1,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD_ARROWS,
    type: "symbol",
    source: MAP_SOURCES.ROUTES,
    minzoom: MAP_ZOOM.ROUTES_MIN,
    filter: ["==", ["get", "direction"], "backward"],
    layout: {
      "symbol-placement": "line",
      "text-field": "◀",
      "symbol-spacing": 80,
      "text-size": 12,
      "text-rotation-alignment": "map",
      "text-keep-upright": true,
    },
    paint: {
      "text-color": MAP_COLORS.ROUTE_MAIN,
      "text-halo-color": MAP_COLORS.LABEL_HALO,
      "text-halo-width": 1,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Hover                                                              */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD_HOVER,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "id"], ""],
    paint: {
      "line-width": 3,
      "line-color": MAP_COLORS.ROUTE_HOVER,
      "line-opacity": 0.9,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD_HOVER,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "id"], ""],
    paint: {
      "line-width": 3,
      "line-color": MAP_COLORS.ROUTE_HOVER,
      "line-opacity": 0.9,
    },
  });
}
