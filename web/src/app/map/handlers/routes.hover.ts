// web/src/app/map/handlers/routes.hover.ts
// Hover-логика для маршрутов.
//
// Ответственность:
// - подсветка конкретного маршрута
// - popup по центру линии
//
// Инварианты:
// - НЕ добавляет слои
// - НЕ трогает source
// - НЕ хранит глобальное состояние
// - hover ТОЛЬКО по id

import maplibregl, { type Map, type MapMouseEvent } from "maplibre-gl";
import type { FilterSpecification } from "maplibre-gl";

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

/**
 * Возвращает midpoint линии для позиционирования popup.
 * Используется ТОЛЬКО для UI.
 */
function getLineMidpoint(line: GeoJSON.LineString): [number, number] {
  const coords = line.coordinates;
  if (!coords.length) return [0, 0];

  const mid = coords[Math.floor(coords.length / 2)];
  return [mid[0], mid[1]];
}

/* ------------------------------------------------------------------ */
/* Hover handlers                                                     */
/* ------------------------------------------------------------------ */

export function attachRouteHoverHandlers(map: Map) {
  let popup: maplibregl.Popup | null = null;
  let activeRouteId: string | null = null;

  const emptyFilter: FilterSpecification = ["==", ["get", "id"], ""];

  /**
   * Применяет hover-фильтр по route id
   */
  function setHover(routeId: string | null) {
    const filter: FilterSpecification =
      routeId === null
        ? emptyFilter
        : ["==", ["get", "id"], routeId];

    map.setFilter("routes-line-forward-hover", filter);
  }

  /**
   * Наведение на маршрут
   */
  function handleEnter(
    e: MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }
  ) {
    const f = e.features?.[0];
    if (!f) return;

    const routeId = String(f.properties?.id ?? "");
    if (!routeId) return;

    activeRouteId = routeId;
    setHover(routeId);

    if (!popup) {
      popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
      });
    }

    const midpoint = getLineMidpoint(f.geometry as GeoJSON.LineString);
    popup
      .setLngLat(midpoint)
      .setText(`Route ${routeId}`)
      .addTo(map);

    map.getCanvas().style.cursor = "pointer";
  }

  /**
   * Уход курсора
   */
  function handleLeave() {
    activeRouteId = null;
    setHover(null);

    popup?.remove();
    map.getCanvas().style.cursor = "";
  }

  /* ------------------------------------------------------------------ */
  /* Event bindings                                                     */
  /* ------------------------------------------------------------------ */

  map.on("mouseenter", "routes-line-forward", handleEnter);
  map.on("mouseleave", "routes-line-forward", handleLeave);

  /* ------------------------------------------------------------------ */
  /* Public API                                                         */
  /* ------------------------------------------------------------------ */

  return {
    /**
     * Восстанавливает hover после setData
     */
    restoreHover() {
      if (activeRouteId) {
        setHover(activeRouteId);
      }
    },
  };
}