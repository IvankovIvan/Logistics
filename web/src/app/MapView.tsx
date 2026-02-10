// File: web/src/app/MapView.tsx
// Module: MapLibre map coordinator.
//
// Ответственность модуля:
// - Создать MapLibre-карту (РОВНО ОДИН раз)
// - Отследить готовность карты и стиля
// - Сообщить наверх, что карта готова (onReady)
// - Делегировать ВСЮ логику работы с картой в MapFacade
//
// Почему это здесь:
// - MapView — точка монтирования карты и только orchestrator
// - Любая бизнес-логика уходит в Facade или UI-компоненты
//
// Инварианты:
// - MapView не знает про sources
// - MapView не знает про layers
// - MapView не знает про hover / popup
// - MapView только orchestrator

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { MapFacade } from "./map/facade/map.facade";
import type { MapBounds } from "./map/transform";
import type { RouteStatus } from "./map/constants";

import { RouteStatusFilter } from "./map/ui/RouteStatusFilter";

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

/**
 * Props, которые MapView получает от родителя.
 *
 * ВАЖНО:
 * - MapView НЕ загружает данные
 * - MapView НЕ трансформирует данные
 * - MapView НЕ хранит состояние данных
 */
type MapViewProps = {
  warehousesGeoJson:
    | GeoJSON.FeatureCollection<
        GeoJSON.Point,
        { id: string; name: string; status: string; quantity: number }
      >
    | null;

  routesGeoJson:
    | GeoJSON.FeatureCollection<
        GeoJSON.LineString,
        { id: string; status: string; from: string; to: string }
      >
    | null;

  /** Границы для initial fitBounds */
  bounds: MapBounds;

  /** Сигнал наверх: карта создана и готова */
  onReady?: () => void;
};

/* ------------------------------------------------------------------ */
/* MapView                                                            */
/* ------------------------------------------------------------------ */

export default function MapView({
  warehousesGeoJson,
  routesGeoJson,
  bounds,
  onReady,
}: MapViewProps) {
  /* ------------------------------------------------------------------ */
  /* Refs                                                              */
  /* ------------------------------------------------------------------ */

  /** DOM-узел, в который будет смонтирована карта */
  const containerRef = useRef<HTMLDivElement | null>(null);

  /** Экземпляр MapLibre.Map (живёт весь lifecycle компонента) */
  const mapRef = useRef<maplibregl.Map | null>(null);

  /** Facade — единая точка управления картой */
  const facadeRef = useRef<MapFacade | null>(null);

  /** Актуальный onReady без перезапуска effect */
  const onReadyRef = useRef(onReady);

  /* ------------------------------------------------------------------ */
  /* State                                                             */
  /* ------------------------------------------------------------------ */

  /**
   * Флаг готовности стиля.
   *
   * ВАЖНО:
   * - MapLibre разрешает addSource/addLayer ТОЛЬКО после загрузки стиля
   */
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
    // Карта создаётся строго один раз
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "/map/base-style.json",
      center: [37.6, 55.75],
      zoom: 4,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");

    mapRef.current = map;
    facadeRef.current = new MapFacade({ map });

    /**
     * Событие load:
     * - карта создана
     * - можно сообщить наверх
     */
    const handleLoad = () => {
      onReadyRef.current?.();
      if (map.isStyleLoaded()) {
        setIsStyleLoaded(true);
      }
    };

    /**
     * Событие style.load:
     * - стиль готов
     * - можно добавлять sources и layers
     */
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
      facadeRef.current = null;
    };
  }, []);

  /* ------------------------------------------------------------------ */
  /* Data → MapFacade synchronization                                   */
  /* ------------------------------------------------------------------ */

  useEffect(() => {
    const facade = facadeRef.current;

    if (!facade || !isStyleLoaded) return;
    if (!warehousesGeoJson || !routesGeoJson) return;

    /**
     * init() — идемпотентен:
     * - первый вызов инициализирует карту
     * - последующие ничего не делают
     */
    facade.init({
      warehousesGeoJson,
      routesGeoJson,
      bounds,
    });

    /**
     * update() — безопасен:
     * - обновляет только данные
     * - не трогает структуру карты
     */
    facade.update({
      routesGeoJson,
    });
  }, [isStyleLoaded, warehousesGeoJson, routesGeoJson, bounds]);

  /* ------------------------------------------------------------------ */
  /* Route filter bridge (UI → Facade)                                   */
  /* ------------------------------------------------------------------ */

  /**
   * Callback из UI (RouteStatusFilter).
   *
   * ВАЖНО:
   * - MapView не знает, КАК фильтруются маршруты
   * - просто прокидывает состояние в Facade
   */
  const handleRouteFilterChange = useCallback(
    (statuses: RouteStatus[]) => {
      facadeRef.current?.setRouteStatusFilter(statuses);
    },
    []
  );

  /* ------------------------------------------------------------------ */

  return (
    <>
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%" }}
      />

      {/* UI-слой поверх карты: фильтры живут отдельно от MapView */}
      <RouteStatusFilter onChange={handleRouteFilterChange} />
    </>
  );
}
