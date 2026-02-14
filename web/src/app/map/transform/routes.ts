// web/src/app/map/transform/routes.ts
//
// Transform-функции маршрутов
//
// Ответственность:
// - API → визуальные features
// - 1 маршрут = 1 линия
// - direction ТОЛЬКО для UI

import type {
  Feature,
  FeatureCollection,
  LineString,
  Position,
} from "geojson";

import {
  getDirectionFromVector,
  type RouteDirection,
} from "../geometry/routes.geometry";

export type RouteInputProps = {
  id: string;
  status: string;
  from: string;
  to: string;
  volume?: number;
};

export type RouteVisualProps = {
  id: string;
  status: string;
  direction: RouteDirection;
  label: string;
  volume?: number;
};

export function buildRouteFeatures(
  routes: FeatureCollection<LineString, RouteInputProps>
): FeatureCollection<LineString, RouteVisualProps> {
  return {
    type: "FeatureCollection",
    features: routes.features.map((f) => {
      const { id, status, volume } = f.properties;

      const [start, end] = f.geometry.coordinates as [
        Position,
        Position
      ];

      const direction = getDirectionFromVector(start, end);
      return {
        type: "Feature",
        geometry: f.geometry, // ⬅️ БЕЗ ИЗМЕНЕНИЙ
        properties: {
          id,
          status,
          direction,
          label: id,
          volume,
        },
      };
    }),
  };
}
