import { fetchJson } from "@/app/map/api";
import type { MapResponse } from "@/app/map/api";

export async function fetchMap(signal?: AbortSignal): Promise<MapResponse> {
  return fetchJson<MapResponse>("/api/analytics/map", signal);
}
