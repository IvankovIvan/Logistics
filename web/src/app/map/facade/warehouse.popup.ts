import type { WarehouseMetadata } from "@/models/analytics";

export function buildWarehousePopupHtml(data: WarehouseMetadata): string {
  const byStatus = data.metrics.by_status ?? [];
  const statusesHtml =
    byStatus.length > 0
      ? byStatus
          .map(
            (s) =>
              `<div>${String(s.status_text)} — ${Number(s.count)} / ${Number(s.sum)}</div>`
          )
          .join("")
      : "<div>Нет данных</div>";

  return `
    <h3>${String(data.name)}</h3>
    <div>Номер: ${Number(data.warehouse_id)}</div>
    <div>Баркодов: ${Number(data.metrics.count)}</div>
    <div>Общее кол-во: ${Number(data.metrics.sum)}</div>
    ${statusesHtml}
    <button id="download-csv">Скачать CSV</button>
  `;
}
