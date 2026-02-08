// routes.geometry.ts
//
// Геометрические утилиты для маршрутов.
//
// Ответственность:
// - вычисление КАНОНИЧЕСКОЙ нормали для пары A↔B
// - построение смещённой геометрии
//
// ВАЖНО:
// - нормаль одна для пары
// - знак смещения зависит от direction

import type { LineString, Position } from "geojson";

export type RouteDirection = "forward" | "backward";

/**
 * Строит смещённую геометрию маршрута.
 */
export function buildShiftedRouteGeometry(
  start: Position,
  end: Position,
  direction: RouteDirection,
  offsetMeters = 20
): LineString {
  // 1️⃣ канонический вектор (одинаков для A↔B)
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