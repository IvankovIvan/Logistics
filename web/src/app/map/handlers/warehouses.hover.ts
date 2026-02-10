// web/src/app/map/handlers/warehouses.hover.tsы
// Hover-логика для складов (точки).
//
// Ответственность:
// - popup при наведении
// - управление курсором
//
// Инварианты:
// - НЕ добавляет слои
// - НЕ меняет source
// - НЕ хранит глобальное состояние
// - работает только через map API

import maplibregl, { type Map, type MapMouseEvent } from "maplibre-gl";

/**
 * Подключает hover-обработчики для слоя складов.
 *
 * Требования:
 * - слой "warehouses-layer" уже добавлен
 *
 * @param map Экземпляр MapLibre
 */
export function attachWarehouseHoverHandlers(map: Map) {
  let popup: maplibregl.Popup | null = null;

  /**
   * Наведение на склад
   */
  function handleEnter(
    e: MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }
  ) {
    const f = e.features?.[0];
    if (!f) return;

    const id = String(f.properties?.id ?? "");
    if (!id) return;

    const [lon, lat] = (f.geometry as GeoJSON.Point).coordinates;

    if (!popup) {
      popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
      });
    }

    popup.setLngLat([lon, lat]).setText(id).addTo(map);
    map.getCanvas().style.cursor = "pointer";
  }

  /**
   * Уход курсора со склада
   */
  function handleLeave() {
    popup?.remove();
    map.getCanvas().style.cursor = "";
  }

  map.on("mouseenter", "warehouses-layer", handleEnter);
  map.on("mouseleave", "warehouses-layer", handleLeave);

  /**
   * API на будущее (если понадобится)
   */
  return {
    detach() {
      map.off("mouseenter", "warehouses-layer", handleEnter);
      map.off("mouseleave", "warehouses-layer", handleLeave);
      popup?.remove();
    },
  };
}
