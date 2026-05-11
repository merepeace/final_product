export type OrderStatus =
  | "pending"
  | "validated"
  | "assigned"
  | "in_transit"
  | "delivered"
  | "cancelled"
  | "failed";

export interface OrdersQueueSnapshot {
  validated_orders_waiting: number;
  idle_agvs: number;
  busy_agvs: number;
  note: string;
}

export interface Order {
  id: number;
  order_name: string;
  product: string;
  qty: number;
  status: OrderStatus;
  agv: string | null;
  priority: number;
  from_location: string;
  to_location: string;
  order_time: string;
  completed_timestamp: string | null;
  confirmed_by: string | null;
}

export interface OrderCreatePayload {
  order_name: string;
  product: string;
  qty: number;
  priority: number;
  from_location: string;
  to_location: string;
}

export interface Product {
  id: string;
  productname: string;
  model: string;
  color: string;
  stock_quantity: number;
  price_usd: number;
  location: string;
  min_stock: number;
}

export type ProductCreatePayload = Omit<Product, "id">;

export interface Zone {
  id: number;
  name: string;
  zone_type: string;
  is_active: boolean;
  is_occupied: boolean;
}

export interface ZoneCreatePayload {
  name: string;
  zone_type: string;
  is_active: boolean;
}

export interface AGV {
  id: number;
  name: string;
  status: "idle" | "busy" | "offline";
  current_order_id: number | null;
  last_active: string | null;
}

export interface AGVUpdatePayload {
  name?: string;
  status?: "idle" | "busy" | "offline";
}

export interface SystemLog {
  id: number;
  timestamp: string;
  level: string;
  source: string;
  message: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
