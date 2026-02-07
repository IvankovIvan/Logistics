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

import { buildAggregatedDirectionalRoutes } from "../transform/routes";
import type { MapBounds } from "../transform";

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
      buildAggregatedDirectionalRoutes(routesGeoJson)
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
      buildAggregatedDirectionalRoutes(data.routesGeoJson)
    );

    this.routeHover?.restoreHover();
  }
}