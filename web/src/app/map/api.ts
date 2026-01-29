// web/src/app/map/api.ts
// Здесь вся работа с API карты: типы ответа + один запрос.
// Зачем: page.tsx и MapView не должны знать, как именно мы ходим в бек.

export type MapWarehouse = {
  id: string;
  name: string;
  status: string;
  lon: number;
  lat: number;
};

export type MapRoute = {
  id: string;
  status: string; // "planned" | "in_transit" | ...
  from: string;
  to: string;
  // Важно: бек отдаёт [[lon,lat],[lon,lat]]
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
async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${url} -> ${res.status} ${res.statusText}\n${text}`);
  }
  return (await res.json()) as T;
}

/**
 * Данные для карты одним запросом.
 * Этот endpoint уже есть в бекенде: /api/map
 */
export async function fetchMap(): Promise<MapResponse> {
  return fetchJson<MapResponse>("/api/map");
}