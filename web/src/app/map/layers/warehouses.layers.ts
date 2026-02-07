// web/src/app/map/layers/warehouses.layers.ts
// Слои складов (точки + подписи)
//
// Ответственность:
// - добавить ВСЕ слои складов
// - ничего не знать про данные, hover, zoom камеры
//
// Инварианты:
// - source "warehouses" УЖЕ существует
// - функция вызывается ровно один раз

import type { Map } from "maplibre-gl";

/**
 * Добавляет слои складов:
 * - circle (точка)
 * - symbol (подпись)
 */
export function addWarehouseLayers(map: Map) {
  /* Основной слой точек */
  map.addLayer({
    id: "warehouses-layer",
    type: "circle",
    source: "warehouses",
    paint: {
      "circle-radius": 6,
      "circle-color": "#2563eb",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff",
    },
  });

  /* Подписи складов */
  map.addLayer({
    id: "warehouses-labels",
    type: "symbol",
    source: "warehouses",
    minzoom: 4,
    layout: {
      "text-field": ["concat", ["get", "name"], " ", ["get", "id"]],
      "text-size": 11,
      "text-anchor": "top",
      "text-offset": [0, 1.1],
    },
    paint: {
      "text-color": "#334155",
      "text-halo-color": "#ffffff",
      "text-halo-width": 1,
    },
  });
}