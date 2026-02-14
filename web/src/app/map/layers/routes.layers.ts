// routes.layers.ts

import type { Map } from "maplibre-gl";
import {
  MAP_LAYERS,
  MAP_SOURCES,
  MAP_ZOOM,
  MAP_COLORS,
  ROUTE_OFFSETS,
  ROUTE_MIN_W,
  ROUTE_MAX_W,
  ROUTE_K,
  ROUTE_STATUS_COLORS,
  TEXT_OFFSET_ARROWS,
  TEXT_SIZE_ARROWS,
} from "../constants";

export function addRouteLayers(map: Map): void {
  const routeWidthExpression = [
    "min",
    ROUTE_MAX_W,
    [
      "max",
      ROUTE_MIN_W,
      [
        "+",
        ROUTE_MIN_W,
        [
          "*",
          ROUTE_K,
          ["/", ["ln", ["+", ["get", "volume"], 1]], ["ln", 10]],
        ],
      ],
    ],
  ];

  /* ------------------------------------------------------------------ */
  /* Lines                                                              */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "direction"], "forward"],
    minzoom: MAP_ZOOM.ROUTES_MIN,
    paint: {
      "line-width": routeWidthExpression,

      // ⬅️ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ
      // цвет берётся из properties.status
      "line-color": [
        "match",
        ["get", "status"],
        "in_transit", ROUTE_STATUS_COLORS.in_transit,
        "planned", ROUTE_STATUS_COLORS.planned,
        "cancelled", ROUTE_STATUS_COLORS.cancelled,
        "delivered", ROUTE_STATUS_COLORS.delivered,
        ROUTE_STATUS_COLORS.default,
      ],

      "line-offset": ROUTE_OFFSETS,
      "line-opacity": 0.75,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "direction"], "backward"],
    minzoom: MAP_ZOOM.ROUTES_MIN,
    paint: {
      "line-width": routeWidthExpression,
      "line-color": [
        "match",
        ["get", "status"],
        "in_transit", ROUTE_STATUS_COLORS.in_transit,
        "planned", ROUTE_STATUS_COLORS.planned,
        "cancelled", ROUTE_STATUS_COLORS.cancelled,
        "delivered", ROUTE_STATUS_COLORS.delivered,
        ROUTE_STATUS_COLORS.default,
      ],
      "line-offset": ROUTE_OFFSETS,
      "line-opacity": 0.75,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Arrows — ТО ЖЕ СМЕЩЕНИЕ                                             */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD_ARROWS,
    type: "symbol",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "direction"], "forward"],
    minzoom: MAP_ZOOM.ROUTES_MIN,
    layout: {
      "symbol-placement": "line",
      "text-field": "▶ ▶ ▶",
      "symbol-spacing": 80,
      "text-size": TEXT_SIZE_ARROWS,
      "text-rotation-alignment": "map",
      "text-keep-upright": true,
      // смещаем стрелку на ту же сторону, что и линия
      "text-offset": [0,TEXT_OFFSET_ARROWS],
    },
    paint: {
      "text-color": MAP_COLORS.ROUTE_MAIN,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD_ARROWS,
    type: "symbol",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "direction"], "backward"],
    minzoom: MAP_ZOOM.ROUTES_MIN,
    layout: {
      "symbol-placement": "line",
      "text-field": "◀ ◀ ◀",
      "symbol-spacing": 80,
      "text-size": TEXT_SIZE_ARROWS,
      "text-rotation-alignment": "map",
      "text-keep-upright": true,
      // смещаем стрелку на ту же сторону, что и линия
      "text-offset": [0,TEXT_OFFSET_ARROWS],
    },
    paint: {
      "text-color": MAP_COLORS.ROUTE_MAIN,
    },
  });


  /* ------------------------------------------------------------------ */
  /* Hover                                                             */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.ROUTES_FORWARD_HOVER,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "id"], ""],
    paint: {
      "line-width": 3,
      "line-color": MAP_COLORS.ROUTE_HOVER,
      "line-offset": 2,
      "line-opacity": 0.9,
    },
  });

  map.addLayer({
    id: MAP_LAYERS.ROUTES_BACKWARD_HOVER,
    type: "line",
    source: MAP_SOURCES.ROUTES,
    filter: ["==", ["get", "id"], ""], // пусто по умолчанию
    paint: {
      "line-width": 3,
      "line-color": MAP_COLORS.ROUTE_HOVER,
      "line-offset": ROUTE_OFFSETS,
      "line-opacity": 0.9,
    },
  });
}
