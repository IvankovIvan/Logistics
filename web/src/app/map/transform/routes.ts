// web/src/app/map/transform/routes.ts
// Transform-функции для маршрутов.
//
// Ответственность модуля:
// - преобразование данных API → данные для визуализации
// - агрегация маршрутов по направлению
//
// ВАЖНО:
// - модуль НЕ знает ничего про MapLibre
// - модуль НЕ меняет контракт API
// - чистые функции (deterministic)

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

export type RouteInputProps = {
  id: string;
  status: string;
  from: string;
  to: string;
};

export type AggregatedRouteProps = {
  direction: "forward" | "backward";
  count: number;
  status: string;
  label: string;
  statuses: string[];
};

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

/**
 * Определяет направление маршрута.
 *
 * Правило (детерминированное, без догадок):
 * - from < to → forward
 * - from > to → backward
 *
 * ВАЖНО:
 * - используется ТОЛЬКО существующие данные
 */
function getDirection(from: string, to: string): "forward" | "backward" {
  return from < to ? "forward" : "backward";
}

/**
 * Выбирает агрегированный статус маршрута.
 *
 * Приоритет:
 * 1. in_transit
 * 2. planned
 * 3. первый из списка
 */
function aggregateStatus(statuses: string[]): string {
  if (statuses.includes("in_transit")) return "in_transit";
  if (statuses.includes("planned")) return "planned";
  return statuses[0];
}

/* ------------------------------------------------------------------ */
/* Public API                                                         */
/* ------------------------------------------------------------------ */

/**
 * Агрегирует маршруты по направлению (from → to).
 *
 * Гарантии:
 * - контракт API не меняется
 * - каждая сторона (forward / backward) — отдельная линия
 * - данные используются ТОЛЬКО для визуализации
 */
export function buildAggregatedDirectionalRoutes(
  routes: GeoJSON.FeatureCollection<
    GeoJSON.LineString,
    RouteInputProps
  >
): GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  AggregatedRouteProps
> {
  type Acc = {
    geometry: GeoJSON.LineString;
    direction: "forward" | "backward";
    statuses: string[];
  };

  const byKey = new Map<string, Acc>();

  for (const feature of routes.features) {
    const { from, to, status } = feature.properties;
    const direction = getDirection(from, to);

    const key = `${from}__${to}__${direction}`;

    const geometry: GeoJSON.LineString =
      direction === "forward"
        ? feature.geometry
        : {
            type: "LineString" as const,
            coordinates: [...feature.geometry.coordinates].reverse(),
          };

    if (!byKey.has(key)) {
      byKey.set(key, {
        geometry,
        direction,
        statuses: [],
      });
    }

    byKey.get(key)!.statuses.push(status);
  }

  const features: GeoJSON.Feature<
    GeoJSON.LineString,
    AggregatedRouteProps
  >[] = [];

  for (const acc of byKey.values()) {
    const count = acc.statuses.length;

    features.push({
      type: "Feature",
      geometry: acc.geometry,
      properties: {
        direction: acc.direction,
        count,
        statuses: acc.statuses,
        status: aggregateStatus(acc.statuses),
        label: count > 1 ? `×${count}` : "1",
      },
    });
  }

  return {
    type: "FeatureCollection",
    features,
  };
}