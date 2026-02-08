// routes.ts
//
// Transform-функции для маршрутов.
//
// Ответственность:
// - API → визуальные route features
// - 1 маршрут = 1 линия
// - direction нужен ТОЛЬКО для UI

import type {
  Feature,
  FeatureCollection,
  LineString,
  Position,
} from "geojson";

import {
  buildShiftedRouteGeometry,
  type RouteDirection,
} from "../geometry/routes.geometry";

export type RouteInputProps = {
  id: string;
  status: string;
  from: string;
  to: string;
};

export type RouteVisualProps = {
  id: string;
  status: string;
  direction: RouteDirection;
  label: string;
};

export function buildRouteFeatures(
  routes: FeatureCollection<LineString, RouteInputProps>
): FeatureCollection<LineString, RouteVisualProps> {
  return {
    type: "FeatureCollection",
    features: routes.features.map((f) => {
      const { id, status, from, to } = f.properties;

      const [start, end] = f.geometry.coordinates as [
        Position,
        Position
      ];

      // direction ДЕТЕРМИНИРОВАННЫЙ, по API
      const direction: RouteDirection =
        from < to ? "forward" : "backward";

      const geometry = buildShiftedRouteGeometry(
        start,
        end,
        direction
      );

      console.log("ROUTE", id, { direction, start, end });

      return {
        type: "Feature",
        geometry,
        properties: {
          id,
          status,
          direction,
          label: id,
        },
      };
    }),
  };
}