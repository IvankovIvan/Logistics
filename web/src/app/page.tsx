// Module: экран “текущее состояние логистики” (оркестратор).
//
// Роль файла:
// - не знает ничего про MapLibre (SDK-логики здесь быть не должно)
// - связывает: data-layer (useMapPolling) → transform-layer (GeoJSON/bounds) → render-layer (MapView)
// - показывает soft-ошибку баннером, но не “роняет” карту и данные
//
// Инварианты экрана:
// - фронт делает ОДИН запрос к /api/map (дальше может быть polling, но всё равно только этот endpoint)
// - нет фильтров/истории/аналитики — только “на сейчас”
// - при ошибках данные не пропадают (soft errors)

"use client";

import { useMemo, useState } from "react";

import MapView from "./MapView";
import { useMapPolling } from "./map/useMapPolling";
import { computeBounds, toRoutesGeoJson, toWarehousesGeoJson } from "./map/transform";

/**
 * Читает NEXT_PUBLIC_* переменные и безопасно парсит числа/флаги.
 * В Next.js эти значения подставляются на этапе сборки/старта.
 */
function readPollingConfig() {
  const enabledFlag = (process.env.NEXT_PUBLIC_MAP_POLLING ?? "0").trim();
  const isPollingEnabled = enabledFlag === "1" || enabledFlag.toLowerCase() === "true";

  const intervalRaw = (process.env.NEXT_PUBLIC_MAP_POLL_INTERVAL_MS ?? "").trim();
  const intervalMs = intervalRaw ? Number(intervalRaw) : NaN;

  // pollIntervalMs: undefined = polling выключен (в useMapPolling будет один запрос)
  const pollIntervalMs =
    isPollingEnabled && Number.isFinite(intervalMs) && intervalMs > 0 ? intervalMs : undefined;

  return { pollIntervalMs };
}

/**
 * Формат времени "HH:MM" в локали пользователя, без секунд.
 * Если даты нет — возвращаем "—".
 */
function formatTimeHHMM(d: Date | null): string {
  if (!d) return "—";
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Page() {
  // Карта должна “подняться” до того, как мы начнём грузить данные.
  const [isMapReady, setIsMapReady] = useState(false);

  const { pollIntervalMs } = readPollingConfig();

  // Data-layer:
  // - загружает /api/map
  // - поддерживает soft errors (баннер, но данные не сбрасываются)
  // - lastUpdated меняется только на успешной загрузке
  const { data, error, lastUpdated } = useMapPolling({
    enabled: isMapReady,
    pollIntervalMs,
  });

  // Transform-layer: детерминированные преобразования API → GeoJSON/bounds.
  const warehousesGeoJson = useMemo(
    () => (data ? toWarehousesGeoJson(data.warehouses) : null),
    [data]
  );

  const routesGeoJson = useMemo(() => (data ? toRoutesGeoJson(data.routes) : null), [data]);

  const bounds = useMemo(() => (data ? computeBounds(data.warehouses) : null), [data]);

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      {/* Soft error banner:
          - показываем ошибку, но не убираем карту
          - данные (если были) остаются на экране */}
      {error ? (
        <div
          style={{
            position: "absolute",
            zIndex: 10,
            top: 12,
            left: 12,
            right: 12,
            padding: 12,
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 10,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            whiteSpace: "pre-wrap",
          }}
        >
          {error}
        </div>
      ) : null}

      {/* Last updated:
          - показывает время последнего УСПЕШНОГО обновления
          - при ошибках время не меняется (это часть soft-модели) */}
      <div
        style={{
          position: "absolute",
          zIndex: 10,
          right: 12,
          bottom: 12,
          padding: "6px 10px",
          background: "rgba(255,255,255,0.92)",
          border: "1px solid #e5e7eb",
          borderRadius: 10,
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          fontSize: 12,
        }}
        aria-label="last-updated"
      >
        Updated: {formatTimeHHMM(lastUpdated)}
      </div>

      {/* Render-layer: MapView управляет MapLibre. */}
      <MapView
        warehousesGeoJson={warehousesGeoJson}
        routesGeoJson={routesGeoJson}
        bounds={bounds}
        onReady={() => setIsMapReady(true)}
      />
    </div>
  );
}
