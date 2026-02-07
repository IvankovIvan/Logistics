// File: web/src/app/MapView.tsx
// Module: MapLibre integration only (map lifecycle, layers, and listeners).
//
// Задача модуля:
// - Создать MapLibre-карту ровно один раз.
// - Дождаться готовности карты (load) и сообщить наверх (onReady) — это запускает загрузку данных.
// - Дождаться готовности стиля (style loaded), чтобы безопасно добавлять sources/layers
//   (иначе MapLibre может упасть с "Style is not done loading").
// - Источники/слои/слушатели добавляются ровно один раз.
// - При обновлении данных делаем только setData (без пересоздания карты/слоёв).
//
// Инварианты:
// - init: один раз
// - addSource/addLayer/listeners: один раз
// - update: только setData

"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { type GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FilterSpecification } from "maplibre-gl";

import type { MapBounds } from "./map/transform";

type MapViewProps = {
  // GeoJSON складов (точки). null = данных ещё нет (soft-модель).
  warehousesGeoJson:
    | GeoJSON.FeatureCollection<GeoJSON.Point, { id: string; name: string; status: string }>
    | null;

  // GeoJSON маршрутов (линии). null = данных ещё нет (soft-модель).
  routesGeoJson:
    | GeoJSON.FeatureCollection<
        GeoJSON.LineString,
        { id: string; status: string; from: string; to: string }
      >
    | null;

  // Границы по складам для первого fitBounds. null = нет складов/данных.
  bounds: MapBounds;

  // Сигнал наверх: "карта готова" — можно начинать загрузку данных.
  onReady?: () => void;
};

// Phase 6 (routes aggregation):
// Агрегируем маршруты по направлению from -> to.
// Инварианты:
// - НЕ меняем контракт API
// - НЕ теряем направление
// - используем только существующие данные
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

    // ключ УЧИТЫВАЕТ направление
    const key = `${from}__${to}__${direction}`;

    const geometry: GeoJSON.LineString =
      direction === "forward"
        ? f.geometry
        : {
            type: "LineString" as const,
            coordinates: [...f.geometry.coordinates].reverse(),
          };

    byKey.set(key, {
      geometry,
      direction,
      statuses: [],
    });

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

    // Агрегированный статус (приоритет)
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

// Phase 3 (маршруты):
// Визуальная агрегация ТОЛЬКО по направлению from -> to.
// Инвариант:
// - не теряем направление,
// - не дорисовываем несуществующие стороны,
// - используем только существующие поля данных.
function buildDirectionalRoutes(
  routes: GeoJSON.FeatureCollection<
    GeoJSON.LineString,
    { id: string; status: string; from: string; to: string }
  >
): GeoJSON.FeatureCollection<
  GeoJSON.LineString,
  {
    label: string;
    direction: "forward" | "backward";
  }
> {
  const features: GeoJSON.Feature<
    GeoJSON.LineString,
    { label: string; direction: "forward" | "backward" }
  >[] = [];

  for (const f of routes.features) {
    const { id, from, to } = f.properties;

    // Направление определяем ТОЛЬКО по данным, без догадок.
    // Для консистентности считаем:
    // - from < to  => forward
    // - from > to  => backward
    const [start, end] = f.geometry.coordinates;
    const direction: "forward" | "backward" =
      start[0] === f.geometry.coordinates[0][0] &&
      start[1] === f.geometry.coordinates[0][1]
        ? "forward"
        : "backward";

    features.push({
      type: "Feature",
      geometry: f.geometry,
      properties: {
        label: String(id), // label = значение из существующих данных
        direction,
      },
    });
  }

  return {
    type: "FeatureCollection",
    features,
  };
}

// Phase 4 (маршруты): вычисляем точку по центру линии для tooltip.
// Инвариант: локальное вычисление, без изменения данных.
function getLineMidpoint(line: GeoJSON.LineString): [number, number] {
  const coords = line.coordinates;
  if (coords.length === 0) return [0, 0];

  const midIndex = Math.floor(coords.length / 2);
  const p = coords[midIndex];

  // Position -> [number, number]
  return [p[0], p[1]];
}

export default function MapView({ warehousesGeoJson, routesGeoJson, bounds, onReady }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const warehousePopupRef = useRef<maplibregl.Popup | null>(null);
  const routePopupRef = useRef<maplibregl.Popup | null>(null);
  const routeHoverLabelRef = useRef<string | null>(null);
  const routeHoverDirectionRef = useRef<"forward" | "backward" | null>(null);

  // Флаг "мы уже добавили sources/layers/listeners" — чтобы не дублировать.
  const hasSourcesRef = useRef(false);

  // Держим актуальный onReady без включения его в зависимости init-effect.
  // Иначе при каждом ререндере с новой функцией можно случайно дергать жизненный цикл карты.
  const onReadyRef = useRef<MapViewProps["onReady"]>(onReady);
  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  // Это НЕ "карта создана", а именно "стиль готов" (можно addSource/addLayer).
  const [isStyleLoaded, setIsStyleLoaded] = useState(false);

  useEffect(() => {
    // Инициализируем карту только один раз.
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      // Phase 1: используем локальный базовый стиль (контроль стиля в проекте).
      style: "/map/base-style.json",
      center: [37.6, 55.75],
      zoom: 4,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    // 1) Стабильный сигнал "карта загрузилась" — используем, чтобы разрешить загрузку данных наверху.
    const handleLoad = () => {
      onReadyRef.current?.();
      // Если стиль уже успел загрузиться — отмечаем сразу.
      if (map.isStyleLoaded()) setIsStyleLoaded(true);
    };

    // 2) Отдельно отслеживаем готовность стиля.
    // Некоторые конфигурации могут иметь стиль уже загруженным к моменту подписки,
    // поэтому проверяем isStyleLoaded() и не полагаемся только на событие.
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

  useEffect(() => {
    const map = mapRef.current;

    // Ничего не делаем, пока:
    // - карта не создана,
    // - стиль не готов,
    // - нет данных (soft-модель: на ошибках данные не сбрасываем в null).
    if (!map || !isStyleLoaded) return;
    if (!warehousesGeoJson || !routesGeoJson) return;

    // Первый успешный приход данных: создаём sources + layers + listeners.
    if (!hasSourcesRef.current) {
      // Доп.страховка: addSource/addLayer только при реально готовом стиле.
      if (!map.isStyleLoaded()) return;

      // Sources (GeoJSON)
      map.addSource("warehouses", { type: "geojson", data: warehousesGeoJson });
      // Phase 3: визуальная агрегация маршрутов выполняется перед рендером,
      // но данные не изменяются (только setData на derived source).
      map.addSource("routes", {
        type: "geojson",
        data: buildAggregatedDirectionalRoutes(routesGeoJson),
      });

      // Слой складов (точки)
      map.addLayer({
        id: "warehouses-layer",
        type: "circle",
        source: "warehouses",
        paint: {
          "circle-radius": 6,
          "circle-color": [
            "match",
            ["get", "status"],
            "active",
            "#2563eb",
            "maintenance",
            "#f59e0b",
            "closed",
            "#6b7280",
            "#2563eb",
          ],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      // Phase 2 (подписи складов): отдельный symbol слой для short name + номер.
      // Инвариант: подписи допускают коллизии (text-allow-overlap: false) и могут скрываться на малом зуме.
      map.addLayer({
        id: "warehouses-labels",
        type: "symbol",
        source: "warehouses",
        minzoom: 4,
        layout: {
          "text-field": ["concat", ["get", "name"], " ", ["get", "id"]],
          "text-size": 11,
          "text-allow-overlap": false,
          "text-ignore-placement": false,
          "text-anchor": "top",
          "text-offset": [0, 1.1],
        },
        paint: {
          "text-color": "#334155",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1,
        },
      });

      // Phase 3 (маршруты):
      // Разведение направлений ТОЛЬКО по существующим данным.
      // Если направления нет — линия не рисуется (сторона пустая).
      map.addLayer({
        id: "routes-line-forward",
        type: "line",
        source: "routes",
        minzoom: 3,
        filter: ["==", ["get", "direction"], "forward"],
        paint: {
          "line-width": 2,
          "line-opacity": 0.75,
          "line-color": "#64748b",
          "line-offset": 2, // forward -> одна сторона
        },
      });

      map.addLayer({
        id: "routes-line-backward",
        type: "line",
        source: "routes",
        minzoom: 3,
        filter: ["==", ["get", "direction"], "backward"],
        paint: {
          "line-width": 2,
          "line-opacity": 0.75,
          "line-color": "#64748b",
          "line-offset": -2, // backward -> другая сторона
        },
      });

      // Phase 4 (hover): используем отдельные hover-слои, а не feature-state,
      // потому что feature-state требует id на фичах (это бы меняло GeoJSON).
      map.addLayer({
        id: "routes-line-forward-hover",
        type: "line",
        source: "routes",
        minzoom: 3,
        filter: ["==", ["get", "label"], ""],
        paint: {
          "line-width": 3,
          "line-opacity": 0.9,
          "line-color": "#1f2937",
          "line-offset": 2,
        },
      });

      map.addLayer({
        id: "routes-line-backward-hover",
        type: "line",
        source: "routes",
        minzoom: 3,
        filter: ["==", ["get", "label"], ""],
        paint: {
          "line-width": 3,
          "line-opacity": 0.9,
          "line-color": "#1f2937",
          "line-offset": -2,
        },
      });

      // Phase 3 (подпись маршрута): число по центру линии, отдельный symbol layer.
      map.addLayer({
        id: "routes-labels",
        type: "symbol",
        source: "routes",
        minzoom: 5,
        layout: {
          "symbol-placement": "line",
          "text-field": ["get", "label"],
          "text-size": 11,
          "text-allow-overlap": false,
          "text-ignore-placement": false,
          "text-rotation-alignment": "map",
          "text-keep-upright": true,
        },
        paint: {
          "text-color": "#475569",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1,
        },
      });

      const emptyFilter: FilterSpecification = ["==", ["get", "label"], ""];

      // Phase 4 (hover): подсветка конкретной линии + tooltip по центру.
      const setRouteHover = (
        direction: "forward" | "backward",
        label: string | null
      ) => {
        const hoverFilter: FilterSpecification =
          label === null
            ? emptyFilter
            : [
                "all",
                ["==", ["get", "direction"], direction],
                ["==", ["get", "label"], label],
              ];

        if (direction === "forward") {
          map.setFilter("routes-line-forward-hover", hoverFilter);
          map.setFilter("routes-line-backward-hover", emptyFilter);
        } else {
          map.setFilter("routes-line-backward-hover", hoverFilter);
          map.setFilter("routes-line-forward-hover", emptyFilter);
        }
      };

      const handleRouteEnter = (
        direction: "forward" | "backward",
        e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }
      ) => {
        const f = e.features?.[0];
        if (!f) return;

        const props = (f.properties ?? {}) as { label?: string };
        const label = props.label ? String(props.label) : "";
        if (!label) return;

        routeHoverLabelRef.current = label;
        routeHoverDirectionRef.current = direction;
        setRouteHover(direction, label);

        const midpoint = getLineMidpoint(f.geometry as GeoJSON.LineString);
        if (!routePopupRef.current) {
          routePopupRef.current = new maplibregl.Popup({
            closeButton: false,
            closeOnClick: false,
          });
        }

        routePopupRef.current.setLngLat(midpoint).setText(`Route ${label}`).addTo(map);
        map.getCanvas().style.cursor = "pointer";
      };

      const handleRouteLeave = () => {
        routeHoverLabelRef.current = null;
        routeHoverDirectionRef.current = null;
        setRouteHover("forward", null);
        setRouteHover("backward", null);
        routePopupRef.current?.remove();
        map.getCanvas().style.cursor = "";
      };

      map.on("mouseenter", "routes-line-forward", (e) => handleRouteEnter("forward", e));
      map.on("mouseenter", "routes-line-backward", (e) => handleRouteEnter("backward", e));
      map.on("mouseleave", "routes-line-forward", handleRouteLeave);
      map.on("mouseleave", "routes-line-backward", handleRouteLeave);

      // Phase 2 (hover tooltip): показываем только число (id из текущих данных), без изменения стиля точки.
      const handleWarehouseEnter = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
        const f = e.features?.[0];
        if (!f) return;

        const props = (f.properties ?? {}) as { id?: string };
        const id = props.id ? String(props.id) : "";
        if (!id) return;

        const coords = (f.geometry as GeoJSON.Point).coordinates as [number, number];
        if (!warehousePopupRef.current) {
          warehousePopupRef.current = new maplibregl.Popup({
            closeButton: false,
            closeOnClick: false,
          });
        }

        warehousePopupRef.current.setLngLat(coords).setText(id).addTo(map);
        map.getCanvas().style.cursor = "pointer";
      };

      const handleWarehouseLeave = () => {
        warehousePopupRef.current?.remove();
        map.getCanvas().style.cursor = "";
      };

      map.on("mouseenter", "warehouses-layer", handleWarehouseEnter);
      map.on("mouseleave", "warehouses-layer", handleWarehouseLeave);

      // Автозум только один раз — при первом успешном добавлении данных.
      // Это предотвращает “дёргание камеры” при будущих обновлениях данных.
      if (bounds) {
        map.fitBounds(bounds, { padding: 80 });
      }

      hasSourcesRef.current = true;
      return;
    }

    // Дальше: только обновляем данные в существующих sources (без пересоздания слоёв).
    const warehousesSource = map.getSource("warehouses") as GeoJSONSource | undefined;
    const routesSource = map.getSource("routes") as GeoJSONSource | undefined;

    warehousesSource?.setData(warehousesGeoJson);
    routesSource?.setData(buildAggregatedDirectionalRoutes(routesGeoJson));

    // Phase 4: сохраняем hover-состояние при обновлении данных (только setData).
    if (routeHoverLabelRef.current && routeHoverDirectionRef.current) {
      const label = routeHoverLabelRef.current;
      const direction = routeHoverDirectionRef.current;

      const activeFilter: FilterSpecification = [
        "all",
        ["==", ["get", "direction"], direction],
        ["==", ["get", "label"], label],
      ];

      const emptyFilter: FilterSpecification = ["==", ["get", "label"], ""];

      if (direction === "forward") {
        map.setFilter("routes-line-forward-hover", activeFilter);
        map.setFilter("routes-line-backward-hover", emptyFilter);
      } else {
        map.setFilter("routes-line-backward-hover", activeFilter);
        map.setFilter("routes-line-forward-hover", emptyFilter);
      }
    }
  }, [isStyleLoaded, warehousesGeoJson, routesGeoJson, bounds]);

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
}
