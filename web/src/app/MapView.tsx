// Module: MapLibre integration only (map lifecycle, layers, and listeners).
//
// Задача модуля:
// - Создать MapLibre-карту ровно один раз.
// - Дождаться готовности карты (load) и сообщить наверх (onReady) — это запускает загрузку данных.
// - Дождаться готовности стиля (style loaded), чтобы безопасно добавлять sources/layers
//   (иначе MapLibre может упасть с "Style is not done loading").
// - Источники/слои/слушатели добавляются ровно один раз.
// - При обновлении данных делаем только setData (без пересоздания карты/слоёв).

"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl, { type GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

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

export default function MapView({ warehousesGeoJson, routesGeoJson, bounds, onReady }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

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
      style: "https://demotiles.maplibre.org/style.json",
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
      map.addSource("routes", { type: "geojson", data: routesGeoJson });

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

      // Слой маршрутов (линии)
      map.addLayer({
        id: "routes-line",
        type: "line",
        source: "routes",
        paint: {
          "line-width": 3,
          "line-opacity": 0.9,
          "line-color": [
            "match",
            ["get", "status"],
            "in_transit",
            "#16a34a",
            "planned",
            "#f59e0b",
            "#6b7280",
          ],
        },
      });

      // Popup по клику на маршрут
      map.on("click", "routes-line", (e) => {
        const f = e.features?.[0];
        if (!f || !f.properties) return;
        const p = f.properties as any;

        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setText(`Shipment ${p.id} (${p.status}) ${p.from} -> ${p.to}`)
          .addTo(map);
      });

      // Курсор “pointer” на линиях
      map.on("mouseenter", "routes-line", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "routes-line", () => (map.getCanvas().style.cursor = ""));

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
    routesSource?.setData(routesGeoJson);
  }, [isStyleLoaded, warehousesGeoJson, routesGeoJson, bounds]);

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
}