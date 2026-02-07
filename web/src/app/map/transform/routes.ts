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
 * ПРАВИЛО (детерминированное):
 * - направление берётся ИСКЛЮЧИТЕЛЬНО из данных from → to
 *
 * Мы не:
 * - не сортируем
 * - не нормализуем
 * - не гадаем
 */
function getDirection(from: string, to: string): "forward" | "backward" {
  return "forward";
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
 * Агрегирует маршруты по НАПРАВЛЕНИЮ (from → to).
 *
 * Гарантии:
 * - каждый маршрут A → B — отдельная линия
 * - маршрут B → A — отдельная линия
 * - геометрия НЕ МЕНЯЕТСЯ
 * - стрелки всегда смотрят правильно
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

    // КЛЮЧ = НАПРАВЛЕНИЕ КАК В API
    const key = `${from}__${to}`;

    if (!byKey.has(key)) {
      byKey.set(key, {
        geometry: feature.geometry, // НЕ трогаем координаты
        direction: "forward",
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