// file: web/src/app/map/layers/routes.layers.ts
// routes.layers.ts
// Отвечает ТОЛЬКО за добавление слоёв маршрутов на карту.
//
// Инварианты:
// - НЕ трогает sources (ожидается source "routes")
// - НЕ хранит состояние
// - НЕ вешает события
// - добавляет слои РОВНО ОДИН РАЗ
//
// Все визуальные решения маршрутов живут здесь.

import type { Map } from "maplibre-gl";

/**
 * Добавляет ВСЕ слои маршрутов:
 * - forward / backward
 * - hover
 * - labels
 *
 * Требования:
 * - source "routes" уже должен существовать
 */
export function addRouteLayers(map: Map) {
  // ─────────────────────────────
  // Основные линии — forward
  // ─────────────────────────────
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
      "line-opacity": 0.75,
      "line-color": [
        "match",
        ["get", "status"],
        "in_transit", "#2563eb",
        "planned",    "#f59e0b",
        "delivered",  "#16a34a",
        "#64748b",
      ],
      "line-offset": 2,
      "line-dasharray": [
        "case",
        ["==", ["get", "status"], "planned"],
        ["literal", [2, 2]],
        ["literal", [1, 0]],
      ],
    },
  });

  // ─────────────────────────────
  // Основные линии — backward
  // ─────────────────────────────
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
      "line-opacity": 0.75,
      "line-color": [
        "match",
        ["get", "status"],
        "in_transit", "#2563eb",
        "planned",    "#f59e0b",
        "delivered",  "#16a34a",
        "#64748b",
      ],
      "line-offset": -2,
      "line-dasharray": [
        "case",
        ["==", ["get", "status"], "planned"],
        ["literal", [2, 2]],
        ["literal", [1, 0]],
      ],
    },
  });

  // ─────────────────────────────
  // Hover — forward
  // ─────────────────────────────
  map.addLayer({
    id: "routes-line-forward-hover",
    type: "line",
    source: "routes",
    minzoom: 3,
    filter: ["==", ["get", "label"], ""],
    paint: {
      "line-width": 3,
      "line-opacity": 0.9,
      "line-color": "#1f2937",
      "line-offset": 2,
    },
  });

  // ─────────────────────────────
  // Hover — backward
  // ─────────────────────────────
  map.addLayer({
    id: "routes-line-backward-hover",
    type: "line",
    source: "routes",
    minzoom: 3,
    filter: ["==", ["get", "label"], ""],
    paint: {
      "line-width": 3,
      "line-opacity": 0.9,
      "line-color": "#1f2937",
      "line-offset": -2,
    },
  });

  // ─────────────────────────────
  // Подписи маршрутов (×N)
  // ─────────────────────────────
  map.addLayer({
    id: "routes-labels",
    type: "symbol",
    source: "routes",
    minzoom: 5,
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
      "text-color": "#475569",
      "text-halo-color": "#ffffff",
      "text-halo-width": 1,
    },
  });
}