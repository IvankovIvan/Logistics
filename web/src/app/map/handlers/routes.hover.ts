// file: web/src/app/map/handlers/routes.hover.ts
// routes.hover.ts
// Hover-логика для маршрутов.
//
// Ответственность:
// - подсветка forward / backward линии
// - управление hover-слоями
// - popup по центру линии
//
// Инварианты:
// - НЕ добавляет слои
// - НЕ трогает source
// - НЕ хранит глобальное состояние
// - работает только через map API

import maplibregl, { type Map, type MapMouseEvent } from "maplibre-gl";
import type { FilterSpecification } from "maplibre-gl";

/**
 * Возвращает midpoint линии для позиционирования popup.
 * Используется ТОЛЬКО для UI, данные не модифицирует.
 */
function getLineMidpoint(line: GeoJSON.LineString): [number, number] {
  const coords = line.coordinates;
  if (coords.length === 0) return [0, 0];

  const mid = coords[Math.floor(coords.length / 2)];
  return [mid[0], mid[1]];
}

/**
 * Подключает hover-обработчики маршрутов.
 *
 * Требования:
 * - слои маршрутов уже добавлены
 * - hover-слои существуют
 *
 * @param map MapLibre instance
 */
export function attachRouteHoverHandlers(map: Map) {
  let popup: maplibregl.Popup | null = null;
  let activeLabel: string | null = null;
  let activeDirection: "forward" | "backward" | null = null;

  const emptyFilter: FilterSpecification = ["==", ["get", "label"], ""];

  /**
   * Применяет hover-фильтр к нужному направлению
   */
  function setHover(
    direction: "forward" | "backward",
    label: string | null
  ) {
    const filter: FilterSpecification =
      label === null
        ? emptyFilter
        : [
            "all",
            ["==", ["get", "direction"], direction],
            ["==", ["get", "label"], label],
          ];

    if (direction === "forward") {
      map.setFilter("routes-line-forward-hover", filter);
      map.setFilter("routes-line-backward-hover", emptyFilter);
    } else {
      map.setFilter("routes-line-backward-hover", filter);
      map.setFilter("routes-line-forward-hover", emptyFilter);
    }
  }

  /**
   * Общий обработчик наведения
   */
  function handleEnter(
    direction: "forward" | "backward",
    e: MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }
  ) {
    const f = e.features?.[0];
    if (!f) return;

    const label = String(f.properties?.label ?? "");
    if (!label) return;

    activeLabel = label;
    activeDirection = direction;
    setHover(direction, label);

    if (!popup) {
      popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
      });
    }

    const midpoint = getLineMidpoint(f.geometry as GeoJSON.LineString);
    popup.setLngLat(midpoint).setText(`Route ${label}`).addTo(map);

    map.getCanvas().style.cursor = "pointer";
  }

  /**
   * Сброс hover-состояния
   */
  function handleLeave() {
    activeLabel = null;
    activeDirection = null;

    setHover("forward", null);
    setHover("backward", null);

    popup?.remove();
    map.getCanvas().style.cursor = "";
  }

  // Подключаем события
  map.on("mouseenter", "routes-line-forward", (e) =>
    handleEnter("forward", e)
  );
  map.on("mouseenter", "routes-line-backward", (e) =>
    handleEnter("backward", e)
  );

  map.on("mouseleave", "routes-line-forward", handleLeave);
  map.on("mouseleave", "routes-line-backward", handleLeave);

  /**
   * Возвращаем API для восстановления hover после setData
   */
  return {
    restoreHover() {
      if (activeLabel && activeDirection) {
        setHover(activeDirection, activeLabel);
      }
    },
  };
}