// web/src/app/map/constants.ts
// Единый источник правды для MapLibre-констант.
//
// Ответственность модуля:
// - IDs sources
// - IDs layers
// - базовые визуальные параметры
//
// ВАЖНО:
// - никаких import из MapLibre
// - только значения

/* ------------------------------------------------------------------ */
/* Sources                                                            */
/* ------------------------------------------------------------------ */

export const MAP_SOURCES = {
  WAREHOUSES: "warehouses",
  ROUTES: "routes",
} as const;

/* ------------------------------------------------------------------ */
/* Layers                                                             */
/* ------------------------------------------------------------------ */

export const MAP_LAYERS = {
  /* Warehouses */
  WAREHOUSES_POINTS: "warehouses-layer",
  WAREHOUSES_LABELS: "warehouses-labels",

  /* Routes */
  ROUTES_FORWARD: "routes-line-forward",
  ROUTES_BACKWARD: "routes-line-backward",

  /* Routes arrows */
  ROUTES_FORWARD_ARROWS: "routes-line-forward-arrows",
  ROUTES_BACKWARD_ARROWS: "routes-line-backward-arrows",

  ROUTES_FORWARD_HOVER: "routes-line-forward-hover",
  ROUTES_BACKWARD_HOVER: "routes-line-backward-hover",

  ROUTES_LABELS: "routes-labels",
} as const;

/* ------------------------------------------------------------------ */
/* Zoom levels                                                        */
/* ------------------------------------------------------------------ */

export const MAP_ZOOM = {
  ROUTES_MIN: 3,
  ROUTE_LABELS_MIN: 5,
  WAREHOUSE_LABELS_MIN: 4,
} as const;

/* ------------------------------------------------------------------ */
/* Visual styles                                                      */
/* ------------------------------------------------------------------ */

export const MAP_COLORS = {
  ROUTE_MAIN: "#838383",
  ROUTE_HOVER: "#1f2937",

  WAREHOUSE_POINT: "#2563eb",
  WAREHOUSE_LABEL: "#334155",

  LABEL_TEXT: "#475569",
  LABEL_HALO: "#ffffff",
} as const;

/* ------------------------------------------------------------------ */
/* Warehouse radius constants                                          */
/* ------------------------------------------------------------------ */
// Project 1.5.a
// Log-scale radius encoding for warehouses:
// radius = clamp(minR + k * log10(quantity + 1), minR, maxR)
// Эти значения являются визуальными инвариантами и
// не должны изменяться без пересмотра project-1.5a-warehouses-geometry.md

export const WAREHOUSE_MIN_R = 4 as const;
export const WAREHOUSE_MAX_R = 18 as const;
export const WAREHOUSE_K = 4 as const;

/* ------------------------------------------------------------------ */
/* Route width constants                                              */
/* ------------------------------------------------------------------ */
// Project 1.6.b
// width = clamp(minW + k * log10(volume + 1), minW, maxW)
export const ROUTE_MIN_W = 1.5 as const;
export const ROUTE_MAX_W = 8 as const;
export const ROUTE_K = 2.5 as const;

/* ------------------------------------------------------------------ */
/* Route offsets                                                      */
/* ------------------------------------------------------------------ */

export const ROUTE_OFFSETS = 2 as const; // pixels

/* ------------------------------------------------------------------ */
/* text-offset offsets ARROWS                                         */
/* ------------------------------------------------------------------ */
export const TEXT_OFFSET_ARROWS = 0.18 as const;

/* ------------------------------------------------------------------ */
/* text-size offsets ARROWS                                         */
/* ------------------------------------------------------------------ */
export const TEXT_SIZE_ARROWS = 8 as const;

/* ------------------------------------------------------------------ */
/* Route status colors (SOURCE OF TRUTH)                               */
/* ------------------------------------------------------------------ */

export const ROUTE_STATUS_COLORS = {
  in_transit: "#2563eb", // синий
  planned: "#f59e0b",    // оранжевый
  cancelled: "#6b7280",  // серый
  delivered: "#16a34a",  // зелёный
  default: "#2563eb",
} as const;

/* ------------------------------------------------------------------ */
/* Route statuses (single source of truth)                            */
/* ------------------------------------------------------------------ */

export const ROUTE_STATUSES = {
  in_transit: "В пути",
  planned: "Запланирован",
  cancelled: "Отменён",
  delivered: "Доставлен",
} as const;

export type RouteStatus = keyof typeof ROUTE_STATUSES;
