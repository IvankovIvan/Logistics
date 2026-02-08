// web/src/app/map/utils/routeFilterPersist.ts
// Persist helpers for route status filters.
//
// Ответственность модуля:
// - хранить / восстанавливать выбранные статусы маршрутов в localStorage
// - валидировать данные против списка статусов
//
// Почему это здесь:
// - persist — это инфраструктурная утилита
// - MapFacade не должен знать про localStorage
// - UI получает готовые данные без MapLibre

import { ROUTE_STATUSES, type RouteStatus } from "../constants";

const STORAGE_KEY = "logistics.routeStatusFilter";

const ALL_STATUSES = Object.keys(ROUTE_STATUSES) as RouteStatus[];

export function loadRouteStatusFilter(): RouteStatus[] {
  if (typeof window === "undefined") return ALL_STATUSES;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return ALL_STATUSES;

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return ALL_STATUSES;

    return parsed.filter(
      (status): status is RouteStatus =>
        ALL_STATUSES.includes(status as RouteStatus)
    );
  } catch {
    return ALL_STATUSES;
  }
}

export function saveRouteStatusFilter(statuses: RouteStatus[]): void {
  if (typeof window === "undefined") return;

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(statuses));
  } catch {
    // localStorage may be unavailable (private mode, quota, etc.)
  }
}
