// routes.geometry.ts
//
// Геометрические утилиты для маршрутов.
//
// Ответственность:
// - вычисление канонического вектора
// - вычисление нормали
// - построение смещённой геометрии
//
// ВАЖНО:
// - нормаль ВСЕГДА одинакова для A↔B
// - знак смещения зависит от фактического направления маршрута

import type { LineString, Position } from "geojson";

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

export type RouteDirection = "forward" | "backward";

/* ------------------------------------------------------------------ */
/* Direction (визуальный, для стрелок)                                */
/* ------------------------------------------------------------------ */

export function getDirectionFromGeometry(
  start: Position,
  end: Position
): RouteDirection {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];

  if (dx !== 0) return dx > 0 ? "forward" : "backward";
  return dy > 0 ? "forward" : "backward";
}

/* ------------------------------------------------------------------ */
/* Geometry shift                                                     */
/* ------------------------------------------------------------------ */

/**
 * Строит смещённую геометрию маршрута.
 *
 * КЛЮЧЕВО:
 * - нормаль считается из КАНОНИЧЕСКОГО вектора
 * - sign зависит от фактического направления маршрута
 */
export function buildShiftedRouteGeometry(
  start: Position,
  end: Position,
  direction: RouteDirection,
  offsetMeters = 20
): LineString {
  // 1️⃣ канонический вектор (один для A↔B)
  const vx = Math.abs(end[0] - start[0]);
  const vy = Math.abs(end[1] - start[1]);

  const len = Math.sqrt(vx * vx + vy * vy) || 1;

  // 2️⃣ каноническая нормаль
  const nx = -vy / len;
  const ny =  vx / len;

  // 3️⃣ знак смещения
  const sign = direction === "forward" ? 1 : -1;

  const k = 1e-5;

  const sx = nx * offsetMeters * k * sign;
  const sy = ny * offsetMeters * k * sign;

  return {
    type: "LineString",
    coordinates: [
      [start[0] + sx, start[1] + sy],
      [end[0] + sx, end[1] + sy],
    ],
  };
}
