// file: web/src/app/components/RouteLegend.tsx

"use client";

import { useState, useEffect } from "react";
import {
  ROUTE_STATUS_COLORS,
  ROUTE_STATUSES,
  type RouteStatus,
} from "../map/constants";

type Props = {
  /** callback в MapFacade */
  onChange: (statuses: RouteStatus[]) => void;
};

/**
 * RouteLegend
 *
 * Ответственность:
 * - показать легенду цветов
 * - дать чекбоксы фильтрации
 *
 * НЕ знает:
 * - про MapLibre
 * - про слои
 */
export function RouteLegend({ onChange }: Props) {
  const [enabled, setEnabled] = useState<RouteStatus[]>(
    Object.keys(ROUTE_STATUSES) as RouteStatus[]
  );

  useEffect(() => {
    onChange(enabled);
  }, [enabled, onChange]);

  function toggle(status: RouteStatus) {
    setEnabled((prev) =>
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
        {(Object.keys(ROUTE_STATUSES) as RouteStatus[]).map((status) => (
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
              checked={enabled.includes(status)}
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