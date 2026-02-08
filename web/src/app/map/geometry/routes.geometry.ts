// web/src/app/map/geometry/routes.geometry.ts
//
// Геометрические утилиты маршрутов
//
// Ответственность:
// - определение визуального направления
//
// ВАЖНО:
// - НИКАКИХ координатных смещений
// - только логика

import type { Position } from "geojson";

export type RouteDirection = "forward" | "backward";

/**
 * Определяет направление по вектору.
 *
 * Правило:
 * - если вектор в 1 или 4 четверти → forward
 * - иначе → backward
 */
export function getDirectionFromVector(
  start: Position,
  end: Position
): RouteDirection {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];

  // 1 или 4 четверть
  if (dx >= 0) return "forward";
  return "backward";
}