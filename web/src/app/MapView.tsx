// File: web/src/app/MapView.tsx
// Module: MapLibre map coordinator.
//
// Ответственность модуля:
// - Инициализация MapLibre карты (ОДИН раз)
// - Контроль жизненного цикла карты и стиля
// - Добавление sources и layers (ОДИН раз)
// - Обновление данных ТОЛЬКО через setData
// - Подключение внешних handlers (hover, popup и т.п.)
//
// Инварианты:
// - карта создаётся один раз
// - sources / layers добавляются один раз
// - никакой UI-логики (hover) внутри — только orchestration

"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { type GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FilterSpecification } from "maplibre-gl";
import { attachWarehouseHoverHandlers } from "./map/handlers/warehouses.hover";

import type { MapBounds } from "./map/transform";
import { attachRouteHoverHandlers } from "./map/handlers/routes.hover";
import { addWarehouseLayers } from "./map/layers/warehouses.layers";
import { addRouteLayers } from "./map/layers/routes.layers";

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

/**
 * Props, которые MapView получает от родителя.
 * MapView НЕ загружает данные сам — только отображает.
 */
type MapViewProps = {
  warehousesGeoJson:
    | GeoJSON.FeatureCollection<
        GeoJSON.Point,
        { id: string; name: string; status: string }
      >
    | null;

  routesGeoJson:
    | GeoJSON.FeatureCollection<
        GeoJSON.LineString,
        { id: string; status: string; from: string; to: string }
      >
    | null;

  bounds: MapBounds;
  onReady?: () => void;
};

/* ------------------------------------------------------------------ */
/* Routes aggregation                                                  */
/* ------------------------------------------------------------------ */

/**
 * Агрегирует маршруты по направлению (from -> to).
 *
 * Гарантии:
 * - контракт API не меняется
 * - направление сохраняется
 * - каждая сторона (forward/backward) — отдельная линия
 *
 * Используется ТОЛЬКО для визуализации.
 */
function buildAggregatedDirectionalRoutes(
  routes: GeoJSON.FeatureCollection<
    GeoJSON.LineString,
    { id: string; status: string; from: string; to: string }
  >
): GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  {
    direction: "forward" | "backward";
    count: number;
    status: string;
    label: string;
    statuses: string[];
  }
> {
  type Acc = {
    geometry: GeoJSON.LineString;
    direction: "forward" | "backward";
    statuses: string[];
  };

  const byKey = new Map<string, Acc>();

  for (const f of routes.features) {
    const { from, to, status } = f.properties;

    const direction: "forward" | "backward" =
      from < to ? "forward" : "backward";

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

  const features: GeoJSON.Feature<
    GeoJSON.LineString,
    {
      direction: "forward" | "backward";
      count: number;
      status: string;
      label: string;
      statuses: string[];
    }
  >[] = [];

  for (const acc of byKey.values()) {
    const count = acc.statuses.length;

    const status = acc.statuses.includes("in_transit")
      ? "in_transit"
      : acc.statuses.includes("planned")
      ? "planned"
      : acc.statuses[0];

    features.push({
      type: "Feature",
      geometry: acc.geometry,
      properties: {
        direction: acc.direction,
        count,
        status,
        statuses: acc.statuses,
        label: count > 1 ? `×${count}` : "1",
      },
    });
  }

  return {
    type: "FeatureCollection",
    features,
  };
}

/* ------------------------------------------------------------------ */
/* MapView component                                                   */
/* ------------------------------------------------------------------ */

export default function MapView({
  warehousesGeoJson,
  routesGeoJson,
  bounds,
  onReady,
}: MapViewProps) {
  /* ---------------- refs ---------------- */

  /** DOM контейнер карты */
  const containerRef = useRef<HTMLDivElement | null>(null);

  /** Экземпляр MapLibre */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /** Флаг: sources и layers уже добавлены */
  const hasSourcesRef = useRef(false);

  /** Храним актуальный onReady без пересоздания effect */
  const onReadyRef = useRef(onReady);

  /** Hover API маршрутов (вынесен в отдельный модуль) */
  const routeHoverRef = useRef<
    ReturnType<typeof attachRouteHoverHandlers> | null
  >(null);

  // Hover API складов (вынесен в отдельный модуль)
  const warehouseHoverRef = useRef<
    ReturnType<typeof attachWarehouseHoverHandlers> | null
  >(null);

  /* ---------------- state ---------------- */

  /** Стиль карты загружен и можно добавлять sources/layers */
  const [isStyleLoaded, setIsStyleLoaded] = useState(false);

  /* ------------------------------------------------------------------ */
  /* Sync onReady                                                       */
  /* ------------------------------------------------------------------ */

  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  /* ------------------------------------------------------------------ */
  /* Map initialization (ONCE)                                          */
  /* ------------------------------------------------------------------ */

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "/map/base-style.json",
      center: [37.6, 55.75],
      zoom: 4,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    const handleLoad = () => {
      onReadyRef.current?.();
      if (map.isStyleLoaded()) setIsStyleLoaded(true);
    };

    const handleStyleLoad = () => {
      setIsStyleLoaded(true);
    };

    map.on("load", handleLoad);

    if (!map.isStyleLoaded()) {
      map.on("style.load", handleStyleLoad);
    } else {
      setIsStyleLoaded(true);
    }

    return () => {
      map.off("load", handleLoad);
      map.off("style.load", handleStyleLoad);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  /* ------------------------------------------------------------------ */
  /* Data → map synchronization                                        */
  /* ------------------------------------------------------------------ */

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isStyleLoaded) return;
    if (!warehousesGeoJson || !routesGeoJson) return;

    /* ---------- first data arrival ---------- */
    if (!hasSourcesRef.current) {
      if (!map.isStyleLoaded()) return;

      /* Sources */
      map.addSource("warehouses", {
        type: "geojson",
        data: warehousesGeoJson,
      });

      map.addSource("routes", {
        type: "geojson",
        data: buildAggregatedDirectionalRoutes(routesGeoJson),
      });

      /* Layers */
      addWarehouseLayers(map);
      addRouteLayers(map);

      /* Handlers */
      routeHoverRef.current = attachRouteHoverHandlers(map);
      warehouseHoverRef.current = attachWarehouseHoverHandlers(map);

      if (bounds) {
        map.fitBounds(bounds, { padding: 80 });
      }

      hasSourcesRef.current = true;
      return;
    }

    /* ---------- updates ---------- */
    const routesSource = map.getSource("routes") as GeoJSONSource | undefined;
    routesSource?.setData(
      buildAggregatedDirectionalRoutes(routesGeoJson)
    );

    routeHoverRef.current?.restoreHover();
  }, [isStyleLoaded, warehousesGeoJson, routesGeoJson, bounds]);

  /* ------------------------------------------------------------------ */

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
}