// web/src/app/map/ui/RouteStatusFilter.tsx
// UI component for route status filtering.
//
// Ответственность компонента:
// - отображает чекбоксы статусов
// - хранит локальное состояние выбранных статусов
// - сохраняет/восстанавливает состояние через localStorage
// - сообщает наверх activeStatuses
//
// Почему это здесь:
// - UI-логика должна жить отдельно от MapView и Facade
// - MapView получает готовый список статусов без знания persist

"use client";

import { useEffect, useState } from "react";
import {
  ROUTE_STATUS_COLORS,
  ROUTE_STATUSES,
  type RouteStatus,
} from "../constants";
import {
  loadRouteStatusFilter,
  saveRouteStatusFilter,
} from "../utils/routeFilterPersist";

type Props = {
  /** callback в MapView */
  onChange: (statuses: RouteStatus[]) => void;
};

const ALL_STATUSES = Object.keys(ROUTE_STATUSES) as RouteStatus[];

export function RouteStatusFilter({ onChange }: Props) {
  const [active, setActive] = useState<RouteStatus[]>(ALL_STATUSES);

  useEffect(() => {
    const stored = loadRouteStatusFilter();
    setActive(stored);
  }, []);

  useEffect(() => {
    saveRouteStatusFilter(active);
    onChange(active);
  }, [active, onChange]);

  function toggle(status: RouteStatus) {
    setActive((prev) =>
      prev.includes(status)
        ? prev.filter((s) => s !== status)
        : [...prev, status]
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        bottom: 16,
        left: 16,
        background: "white",
        padding: 12,
        borderRadius: 8,
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        fontSize: 13,
      }}
    >
      <strong>Маршруты</strong>

      <div style={{ marginTop: 8 }}>
        {ALL_STATUSES.map((status) => (
          <label
            key={status}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 6,
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={active.includes(status)}
              onChange={() => toggle(status)}
            />

            <span
              style={{
                width: 12,
                height: 12,
                background: ROUTE_STATUS_COLORS[status],
                display: "inline-block",
                borderRadius: 2,
              }}
            />

            {ROUTE_STATUSES[status]}
          </label>
        ))}
      </div>
    </div>
  );
}
