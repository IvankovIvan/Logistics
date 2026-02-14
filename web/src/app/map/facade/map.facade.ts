// web/src/app/map/facade/map.facade.ts
//
// Facade над MapLibre.
//
// Ответственность:
// - инкапсулировать ВСЮ механику карты
// - предоставить простой API для MapView
//
// Инварианты:
// - init() вызывается строго один раз
// - update() может вызываться сколько угодно раз
// - Facade НЕ знает про UI и localStorage
// - Facade НЕ меняет GeoJSON, только управляет MapLibre

import type { Map, FilterSpecification } from "maplibre-gl";

import { addMapSources, updateRouteSource } from "../sources/map.sources";
import { addWarehouseLayers } from "../layers/warehouses.layers";
import { addRouteLayers } from "../layers/routes.layers";

import { attachRouteHoverHandlers } from "../handlers/routes.hover";

import { buildRouteFeatures } from "../transform/routes";
import type { MapBounds } from "../transform";

import { MAP_LAYERS, type RouteStatus } from "../constants";

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

function buildRouteLayerFilter(
  direction: "forward" | "backward",
  statuses: RouteStatus[]
): FilterSpecification {
  if (statuses.length === 0) {
    return ["==", ["get", "status"], "__none__"];
  }

  return [
    "all",
    ["==", ["get", "direction"], direction],
    ["in", ["get", "status"], ["literal", statuses]],
  ];
}

/* ------------------------------------------------------------------ */
/* MapFacade                                                          */
/* ------------------------------------------------------------------ */

export class MapFacade {
  private map: Map;
  private initialized = false;

  /**
   * Последний выбранный фильтр.
   *
   * ВАЖНО:
   * - может быть установлен ДО init()
   * - применяется сразу после init()
   */
  private activeRouteStatuses: RouteStatus[] | null = null;

  private routeHover: ReturnType<typeof attachRouteHoverHandlers> | null =
    null;

  constructor({ map }: { map: Map }) {
    this.map = map;
  }

  isInitialized(): boolean {
    return this.initialized;
  }

  /* ------------------------------------------------------------------ */
  /* Init (ONCE)                                                       */
  /* ------------------------------------------------------------------ */

  init(data: {
    warehousesGeoJson: GeoJSON.FeatureCollection<
      GeoJSON.Point,
      { id: string; name: string; status: string; quantity: number }
    >;
    routesGeoJson: GeoJSON.FeatureCollection<
      GeoJSON.LineString,
      { id: string; status: string; from: string; to: string }
    >;
    bounds?: MapBounds;
  }): void {
    if (this.initialized) return;

    const { warehousesGeoJson, routesGeoJson, bounds } = data;

    addMapSources(
      this.map,
      warehousesGeoJson,
      buildRouteFeatures(routesGeoJson)
    );

    addRouteLayers(this.map);
    addWarehouseLayers(this.map);
    

    // Route hover enabled (Project 1.3).
    // Warehouse hover intentionally NOT attached (Project 1.5.a invariant).
    this.routeHover = attachRouteHoverHandlers(this.map);

    if (bounds) {
      this.map.fitBounds(bounds, { padding: 80 });
    }

    this.initialized = true;

    // ✅ КРИТИЧНО: применяем фильтр, если он был установлен раньше
    if (this.activeRouteStatuses) {
      this.applyRouteStatusFilter(this.activeRouteStatuses);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Update                                                            */
  /* ------------------------------------------------------------------ */

  update(data: {
    routesGeoJson: GeoJSON.FeatureCollection<
      GeoJSON.LineString,
      { id: string; status: string; from: string; to: string }
    >;
  }): void {
    if (!this.initialized) return;

    updateRouteSource(
      this.map,
      buildRouteFeatures(data.routesGeoJson)
    );

    if (this.activeRouteStatuses) {
      this.applyRouteStatusFilter(this.activeRouteStatuses);
    }

    this.routeHover?.restoreHover();
  }

  /* ------------------------------------------------------------------ */
  /* Route filter API                                                  */
  /* ------------------------------------------------------------------ */

  setRouteStatusFilter(statuses: RouteStatus[]): void {
    // ✅ ВСЕГДА сохраняем
    this.activeRouteStatuses = statuses;

    if (!this.initialized) return;

    this.applyRouteStatusFilter(statuses);
  }

  private applyRouteStatusFilter(statuses: RouteStatus[]): void {
    const layers = [
      { id: MAP_LAYERS.ROUTES_FORWARD, direction: "forward" as const },
      { id: MAP_LAYERS.ROUTES_BACKWARD, direction: "backward" as const },
      { id: MAP_LAYERS.ROUTES_FORWARD_ARROWS, direction: "forward" as const },
      { id: MAP_LAYERS.ROUTES_BACKWARD_ARROWS, direction: "backward" as const },
    ];

    for (const { id, direction } of layers) {
      this.map.setFilter(
        id,
        buildRouteLayerFilter(direction, statuses)
      );
    }
  }
}
