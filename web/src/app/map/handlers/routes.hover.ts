// web/src/app/map/handlers/routes.hover.ts
//
// Hover-логика для маршрутов.
//
// Ответственность:
// - подсветка конкретного маршрута
// - popup по центру линии
//
// Инварианты:
// - hover ТОЛЬКО по id
// - работает для forward И backward
// - не добавляет слои
// - не трогает source

import maplibregl, { type Map, type MapMouseEvent } from "maplibre-gl";
import type { FilterSpecification } from "maplibre-gl";

/* ------------------------------------------------------------------ */
/* Helpers                                                            */
/* ------------------------------------------------------------------ */

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
   * Применяет hover-фильтр СРАЗУ к обоим hover-слоям
   */
  function setHover(routeId: string | null) {
    const filter: FilterSpecification =
      routeId === null
        ? emptyFilter
        : ["==", ["get", "id"], routeId];

    map.setFilter("routes-line-forward-hover", filter);
    map.setFilter("routes-line-backward-hover", filter);
  }

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

  function handleLeave() {
    activeRouteId = null;
    setHover(null);
    popup?.remove();
    map.getCanvas().style.cursor = "";
  }

  /* ------------------------------------------------------------------ */
  /* Event bindings                                                     */
  /* ------------------------------------------------------------------ */

  // ⚠️ ВАЖНО: подписываемся НА ОБА слоя
  map.on("mouseenter", "routes-line-forward", handleEnter);
  map.on("mouseleave", "routes-line-forward", handleLeave);

  map.on("mouseenter", "routes-line-backward", handleEnter);
  map.on("mouseleave", "routes-line-backward", handleLeave);

  /* ------------------------------------------------------------------ */
  /* Public API                                                         */
  /* ------------------------------------------------------------------ */

  return {
    restoreHover() {
      if (activeRouteId) {
        setHover(activeRouteId);
      }
    },
  };
}