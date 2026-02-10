// Module: карта API-контракты и единый запрос.
//
// Инварианты:
// - один endpoint для карты: /api/map
// - одна точка формирования ошибок (fetchJson)
// - без знаний о UI/MapLibre (это чистый data-layer)
// - cache: "no-store" потому что экран показывает "на сейчас"
// - optional AbortSignal нужен для polling/abort-protection

export type MapWarehouse = {
  id: string;
  name: string;
  status: string;
  lon: number;
  lat: number;
  quantity: number;
};

export type MapRoute = {
  id: string;

  // Сейчас строкой, чтобы не ломать контракт на уровне UI.
  // Можно ужесточить до union-типа позже (planned/in_transit/...).
  status: string;

  from: string;
  to: string;

  // Важно: бек отдаёт [[lon,lat],[lon,lat],...]
  coordinates: [number, number][];
};

export type MapResponse = {
  warehouses: MapWarehouse[];
  routes: MapRoute[];
};

/**
 * Универсальный fetch JSON с нормальной ошибкой.
 * - не кешируем (карта "на сейчас")
 * - при не-200 вытаскиваем текст (чтобы увидеть HTML 502/trace и т.п.)
 */
async function fetchJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { cache: "no-store", signal });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${url} -> ${res.status} ${res.statusText}\n${text}`);
  }

  return (await res.json()) as T;
}

/**
 * Данные для карты одним запросом.
 * Endpoint есть в бекенде: /api/map
 */
export async function fetchMap(signal?: AbortSignal): Promise<MapResponse> {
  return fetchJson<MapResponse>("/api/map", signal);
}
