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

export async function downloadWarehouseCsv(warehouseId: number) {
  const res = await fetch(`/api/analytics/warehouse/${warehouseId}/batches.csv`);

  if (!res.ok) {
    throw new Error("Failed to download CSV");
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `warehouse_${warehouseId}_batches.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
}
