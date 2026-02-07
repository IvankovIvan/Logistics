// file: web/src/app/map/routes/routes.aggregate.ts
// routes.aggregate.ts
// Phase 6: агрегация маршрутов по направлению
// Инварианты:
// - НЕ меняем контракт API
// - НЕ теряем направление
// - используем только существующие данные

export type Direction = "forward" | "backward";

export function buildAggregatedDirectionalRoutes(
  routes: GeoJSON.FeatureCollection<
    GeoJSON.LineString,
    { id: string; status: string; from: string; to: string }
  >
): GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  {
    direction: Direction;
    count: number;
    status: string;
    label: string;
    statuses: string[];
  }
> {
  type Acc = {
    geometry: GeoJSON.LineString;
    direction: Direction;
    statuses: string[];
  };

  const byKey = new Map<string, Acc>();

  for (const f of routes.features) {
    const { from, to, status } = f.properties;

    const direction: Direction = from < to ? "forward" : "backward";
    const key = `${from}__${to}__${direction}`;

    const geometry: GeoJSON.LineString =
      direction === "forward"
        ? f.geometry
        : {
            type: "LineString",
            coordinates: [...f.geometry.coordinates].reverse(),
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

  const features = Array.from(byKey.values()).map(acc => {
    const count = acc.statuses.length;

    const status =
      acc.statuses.includes("in_transit")
        ? "in_transit"
        : acc.statuses.includes("planned")
        ? "planned"
        : acc.statuses[0];

    return {
      type: "Feature",
      geometry: acc.geometry,
      properties: {
        direction: acc.direction,
        count,
        status,
        statuses: acc.statuses,
        label: count > 1 ? `×${count}` : "1",
      },
    } satisfies GeoJSON.Feature<GeoJSON.LineString>;
  });

  return {
    type: "FeatureCollection",
    features,
  };
}