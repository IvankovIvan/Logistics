export interface StatusQuantity {
  status_id: number;
  quantity: number;
}

export interface WarehouseMetrics {
  total: number;
  by_status: StatusQuantity[];
}

export interface MapWarehouse {
  warehouse_id: number;
  name: string;
  lat: number;
  lon: number;
  metrics: WarehouseMetrics;
}

export interface MapResponse {
  warehouses: MapWarehouse[];
  routes: unknown[];
}

export interface WarehouseStatus {
  status_id: number;
  status_text: string;
  count: number;
  sum: number;
}

export interface WarehouseMetricsDetailed {
  count: number;
  sum: number;
  by_status: WarehouseStatus[];
}

export interface WarehouseMetadata {
  warehouse_id: number;
  name: string;
  city: string;
  warehouse_type: string;
  metrics: WarehouseMetricsDetailed;
}
