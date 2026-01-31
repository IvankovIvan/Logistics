// Module: data fetching for the map with optional polling and soft errors.
//
// Инварианты:
// - "soft errors": при ошибках мы НЕ очищаем data и НЕ меняем lastUpdated
//   (экран продолжает показывать последние хорошие данные)
// - lastUpdated обновляется только при успешной загрузке
// - данные могут приходить в любом порядке, но UI должен быть устойчивым
// - защита от гонок: каждый новый запрос абортит предыдущий,
//   чтобы "поздний ответ" не перетёр более свежий

import { useEffect, useRef, useState } from "react";
import { fetchMap, MapResponse } from "./api";

type UseMapPollingOptions = {
  // enabled управляется оркестратором:
  // пока карта не готова — не грузим данные.
  enabled: boolean;

  // Если задан > 0 — включаем polling через setInterval.
  // Если не задан или <= 0 — делаем один запрос.
  pollIntervalMs?: number;
};

type MapPollingState = {
  data: MapResponse | null;
  error: string | null;
  lastUpdated: Date | null;
};

export function useMapPolling({ enabled, pollIntervalMs }: UseMapPollingOptions): MapPollingState {
  const [data, setData] = useState<MapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Храним AbortController текущего запроса (если есть).
  // Это позволяет отменить in-flight запрос при новом polling тикe и при unmount.
  const inFlightRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!enabled) return;

    let mounted = true;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const runFetch = async () => {
      // 1) Отменяем предыдущий запрос, чтобы:
      // - не было гонок ("старый" ответ пришёл позже и затёр "новый")
      // - не копились параллельные запросы при медленной сети
      if (inFlightRef.current) {
        inFlightRef.current.abort();
      }

      const controller = new AbortController();
      inFlightRef.current = controller;

      try {
        // 2) Единственный endpoint: /api/map
        const res = await fetchMap(controller.signal);

        // 3) Защита от setState после unmount
        if (!mounted) return;

        // 4) Успех:
        // - обновляем данные
        // - сбрасываем ошибку
        // - lastUpdated = сейчас
        setData(res);
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        if (!mounted) return;

        // Abort — это не "ошибка данных", это наша нормальная механика.
        // Ничего не логируем и не показываем.
        if (controller.signal.aborted) return;

        console.error(err);

        // 5) Soft error:
        // - не трогаем data и lastUpdated
        // - показываем текст ошибки в баннере
        setError(String(err));
      }
    };

    // Первый запрос сразу, без ожидания интервала.
    runFetch();

    // Polling: один interval, чистится в cleanup.
    if (pollIntervalMs && pollIntervalMs > 0) {
      intervalId = setInterval(runFetch, pollIntervalMs);
    }

    return () => {
      mounted = false;

      if (intervalId) clearInterval(intervalId);

      // Abort обязателен:
      // иначе поздний ответ может попытаться setState после unmount.
      if (inFlightRef.current) {
        inFlightRef.current.abort();
        inFlightRef.current = null;
      }
    };
  }, [enabled, pollIntervalMs]);

  return { data, error, lastUpdated };
}