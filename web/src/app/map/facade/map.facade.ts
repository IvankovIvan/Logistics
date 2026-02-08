// web/src/app/map/facade/map.facade.ts
// Facade над MapLibre.
//
// Ответственность:
// - инкапсулировать ВСЮ механику карты
// - предоставить простой API для MapView
//
// Инварианты:
// - init() вызывается один раз
// - setData() может вызываться сколько угодно раз

import type { Map } from "maplibre-gl";

import { addMapSources, updateRouteSource } from "../sources/map.sources";
import { addWarehouseLayers } from "../layers/warehouses.layers";
import { addRouteLayers } from "../layers/routes.layers";

import { attachRouteHoverHandlers } from "../handlers/routes.hover";
import { attachWarehouseHoverHandlers } from "../handlers/warehouses.hover";

import { buildRouteFeatures } from "../transform/routes";
import type { MapBounds } from "../transform";

import { MAP_LAYERS } from "../constants";
import type { RouteStatus } from "../constants";
import type { FilterSpecification } from "maplibre-gl";


/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

type FacadeDeps = {
  map: Map;
};

/**
 * Данные, которые MapFacade принимает извне.
 * Facade НЕ загружает данные сам.
 */
type WarehousesGeoJson = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  { id: string; name: string; status: string }
>;

type RoutesGeoJson = GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  { id: string; status: string; from: string; to: string }
>;

type FacadeData = {
  warehousesGeoJson: WarehousesGeoJson;
  routesGeoJson: RoutesGeoJson;
  bounds?: MapBounds;
};

/* ------------------------------------------------------------------ */
/* MapFacade                                                           */
/* ------------------------------------------------------------------ */

export class MapFacade {
  private map: Map;
  private initialized = false;

  private routeHover: ReturnType<typeof attachRouteHoverHandlers> | null =
    null;
  private warehouseHover:
    | ReturnType<typeof attachWarehouseHoverHandlers>
    | null = null;

  constructor({ map }: FacadeDeps) {
    this.map = map;
  }

  /* ------------------------------------------------------------------ */
  /* State                                                              */
  /* ------------------------------------------------------------------ */

  /**
   * Возвращает true, если карта уже инициализирована.
   *
   * Используется MapView, чтобы:
   * - вызвать init() строго один раз
   * - далее вызывать только update()
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /* ------------------------------------------------------------------ */
  /* Init (ONCE)                                                        */
  /* ------------------------------------------------------------------ */

  /**
   * Инициализация карты:
   * - добавляет sources
   * - добавляет layers
   * - подключает handlers
   *
   * ВАЖНО:
   * - вызывается строго один раз
   */
  init(data: FacadeData): void {
    if (this.initialized) return;

    const { warehousesGeoJson, routesGeoJson, bounds } = data;

    /* Sources */
    addMapSources(
      this.map,
      warehousesGeoJson,
      buildRouteFeatures(routesGeoJson)
    );

    /* Layers */
    addWarehouseLayers(this.map);
    addRouteLayers(this.map);

    /* Handlers */
    this.routeHover = attachRouteHoverHandlers(this.map);
    this.warehouseHover = attachWarehouseHoverHandlers(this.map);

    /* Initial camera */
    if (bounds) {
      this.map.fitBounds(bounds, { padding: 80 });
    }

    this.initialized = true;
  }

  /* ------------------------------------------------------------------ */
  /* Update                                                             */
  /* ------------------------------------------------------------------ */

  /**
   * Обновляет данные маршрутов.
   *
   * Используется при:
   * - poll
   * - ingest
   * - ручном refresh
   */
  update(data: Pick<FacadeData, "routesGeoJson">): void {
    if (!this.initialized) return;

    updateRouteSource(
      this.map,
      buildRouteFeatures(data.routesGeoJson)
    );

    this.routeHover?.restoreHover();
  }

  /* ------------------------------------------------------------------ */
  /* Route filters                                                      */
  /* ------------------------------------------------------------------ */

  /**
   * Фильтрует маршруты по статусам.
   *
   * @param statuses - список разрешённых статусов
   *
   * ВАЖНО:
   * - работает ТОЛЬКО через setFilter
   * - не меняет данные
   * - применяется ко ВСЕМ route-layer
   */
  setRouteStatusFilter(statuses: RouteStatus[]): void {
    if (!this.initialized) return;

    const filter: FilterSpecification =
      statuses.length === 0
        ? ["==", ["get", "status"], "__none__"] // скрыть всё
        : ["in", ["get", "status"], ["literal", statuses]];

    const routeLayers = [
      MAP_LAYERS.ROUTES_FORWARD,
      MAP_LAYERS.ROUTES_BACKWARD,
      MAP_LAYERS.ROUTES_FORWARD_ARROWS,
      MAP_LAYERS.ROUTES_BACKWARD_ARROWS,
    ];

    for (const layerId of routeLayers) {
      this.map.setFilter(layerId, filter);
    }
  }

}