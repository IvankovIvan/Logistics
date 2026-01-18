"use client";

import { useEffect, useState } from "react";

/**
 * Тип ответа витрины "на сейчас".
 * Важно: структура должна совпадать с API /api/shipments/now.
 */
type ShipmentsNow = {
  total: number;
  by_status: {
    planned: number;
    in_transit: number;
    delivered: number;
    cancelled: number;
  };
};

export default function Page() {
  // data = текущая витрина (null пока не загрузили)
  const [data, setData] = useState<ShipmentsNow | null>(null);

  // loading = чтобы заблокировать кнопку во время запроса
  const [loading, setLoading] = useState(false);

  /**
   * Загружаем витрину с backend.
   * Здесь используем относительный URL "/api/..." — это идёт в nginx,
   * а nginx уже проксирует на FastAPI.
   */
  async function load() {
    setLoading(true);

    // Если API вернёт ошибку, упадём аккуратно (потом сделаем красивее)
    const res = await fetch("/api/shipments/now", { cache: "no-store" });
    const json = await res.json();

    setData(json);
    setLoading(false);
  }

  // При первом открытии страницы сразу грузим данные
  useEffect(() => {
    load();
  }, []);

  // Пока данных нет — показываем простую заглушку
  if (!data) {
    return <main style={{ padding: 32 }}>Загрузка…</main>;
  }

  return (
    <main style={{ padding: 32, fontFamily: "sans-serif" }}>
      <h1>Логистика — витрина “на сейчас”</h1>

      {/* Ручное обновление: безопасный MVP без автопуллинга */}
      <button onClick={load} disabled={loading}>
        {loading ? "Обновляю…" : "Обновить"}
      </button>

      <p>
        <strong>Всего перевозок:</strong> {data.total}
      </p>

      <ul>
        <li>Планируется: {data.by_status.planned}</li>
        <li>В пути: {data.by_status.in_transit}</li>
        <li>Доставлено: {data.by_status.delivered}</li>
        <li>Отменено: {data.by_status.cancelled}</li>
      </ul>
    </main>
  );
}