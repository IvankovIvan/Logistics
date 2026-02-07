// file: web/src/app/map/layers/routes.layers.ts
// Слои маршрутов (линии, hover, подписи)
//
// Ответственность:
// - добавить ВСЕ слои маршрутов
// - визуализация агрегаций (count, direction)
//
// Инварианты:
// - source "routes" УЖЕ существует
// - никакой логики hover внутри

import type { Map } from "maplibre-gl";

/**
 * Добавляет все слои маршрутов:
 * - forward / backward
 * - hover
 * - labels
 */
export function addRouteLayers(map: Map) {
  /* Forward */
  map.addLayer({
    id: "routes-line-forward",
    type: "line",
    source: "routes",
    minzoom: 3,
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
      "line-color": "#2563eb",
      "line-offset": 2,
    },
  });

  /* Backward */
  map.addLayer({
    id: "routes-line-backward",
    type: "line",
    source: "routes",
    minzoom: 3,
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
      "line-color": "#2563eb",
      "line-offset": -2,
    },
  });

  /* Hover layers */
  map.addLayer({
    id: "routes-line-forward-hover",
    type: "line",
    source: "routes",
    filter: ["==", ["get", "label"], ""],
    paint: {
      "line-width": 3,
      "line-color": "#1f2937",
      "line-offset": 2,
    },
  });

  map.addLayer({
    id: "routes-line-backward-hover",
    type: "line",
    source: "routes",
    filter: ["==", ["get", "label"], ""],
    paint: {
      "line-width": 3,
      "line-color": "#1f2937",
      "line-offset": -2,
    },
  });

  /* Labels */
  map.addLayer({
    id: "routes-labels",
    type: "symbol",
    source: "routes",
    minzoom: 5,
    layout: {
      "symbol-placement": "line",
      "text-field": ["get", "label"],
      "text-size": 11,
    },
    paint: {
      "text-color": "#475569",
      "text-halo-color": "#ffffff",
      "text-halo-width": 1,
    },
  });
}