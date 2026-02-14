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
// - радиус кодирует quantity ТОЛЬКО через expression (Project 1.5.a)

import type { ExpressionSpecification, Map } from "maplibre-gl";
import {
  MAP_LAYERS,
  MAP_SOURCES,
  MAP_ZOOM,
  MAP_COLORS,
  WAREHOUSE_K,
  WAREHOUSE_MAX_R,
  WAREHOUSE_MIN_R,
} from "../constants";

/* ------------------------------------------------------------------ */
/* Radius expression (Project 1.5.a)                                  */
/* ------------------------------------------------------------------ */

/**
 * Строит expression для circle-radius.
 *
 * Формула (инвариант):
 *
 * radius = clamp(
 *   minR + k * log10(quantity + 1),
 *   minR,
 *   maxR
 * )
 *
 * Где:
 * log10(x) = ln(x) / ln(10)
 *
 * ДОПОЛНИТЕЛЬНАЯ ЗАЩИТА:
 * quantity всегда ≥ 0 по контракту backend.
 * Но если backend нарушит контракт —
 * мы принудительно ограничиваем значение:
 *
 * safeQuantity = max(0, quantity)
 *
 * Это не бизнес-логика.
 * Это исключительно защита визуального слоя.
 */
export function buildWarehouseRadiusExpression(): ExpressionSpecification {
  return [
    "min",
    WAREHOUSE_MAX_R,
    [
      "max",
      WAREHOUSE_MIN_R,
      [
        "+",
        WAREHOUSE_MIN_R,
        [
          "*",
          WAREHOUSE_K,
          [
            "/",
            [
              "ln",
              [
                "+",
                [
                  "max",
                  0,
                  ["get", "quantity"], // защита от отрицательных значений
                ],
                1,
              ],
            ],
            Math.log(10),
          ],
        ],
      ],
    ],
  ];
}


/* ------------------------------------------------------------------ */
/* Layer registration                                                  */
/* ------------------------------------------------------------------ */

/**
 * Добавляет слои складов на карту.
 *
 * Слои:
 * - circle: визуальная точка склада (геометрия + радиус)
 * - symbol: подпись склада (выключена в 1.5.a)
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
      // Радиус кодирует quantity
      "circle-radius": buildWarehouseRadiusExpression(),

      // Цвет НЕ кодирует quantity (инвариант 1.5.a)
      "circle-color": MAP_COLORS.WAREHOUSE_POINT,

      // Обводка статична
      "circle-stroke-width": 2,
      "circle-stroke-color": MAP_COLORS.LABEL_HALO,
    },
  });

  /* ------------------------------------------------------------------ */
  /* Warehouses: labels (reserved for 1.5.b)                            */
  /* ------------------------------------------------------------------ */

  map.addLayer({
    id: MAP_LAYERS.WAREHOUSES_LABELS,
    type: "symbol",
    source: MAP_SOURCES.WAREHOUSES,
    minzoom: MAP_ZOOM.WAREHOUSE_LABELS_MIN,

    layout: {
      // В 1.5.a подписи ЗАПРЕЩЕНЫ → слой выключен
      visibility: "none",

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