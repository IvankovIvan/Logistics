import { fetchJson } from "@/app/map/api";
import {
  MapResponse,
  WarehouseMetadata,
} from "@/models/analytics";

export async function fetchMap(signal?: AbortSignal): Promise<MapResponse> {
  return fetchJson("/api/analytics/map", signal);
}

export async function fetchWarehouse(
  warehouseId: number
): Promise<WarehouseMetadata> {
  const res = await fetch(`/api/analytics/warehouse/${warehouseId}`);
  if (!res.ok) {
    throw new Error("Failed to fetch warehouse");
  }
  return res.json();
}

export function downloadWarehouseCsv(warehouseId: number): void {
  window.open(`/api/analytics/warehouse/${warehouseId}/batches.csv`);
}
