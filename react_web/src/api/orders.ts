import { api } from "./client";
import type { Order, OrderCreatePayload, OrdersQueueSnapshot } from "../types";

export async function listOrders(): Promise<Order[]> {
  const { data } = await api.get<Order[]>("/orders/");
  return data;
}

export async function getOrdersQueue(): Promise<OrdersQueueSnapshot> {
  const { data } = await api.get<OrdersQueueSnapshot>("/orders/queue");
  return data;
}

export async function getOrder(id: number): Promise<Order> {
  const { data } = await api.get<Order>(`/orders/${id}`);
  return data;
}

export async function createOrder(payload: OrderCreatePayload): Promise<Order> {
  const { data } = await api.post<Order>("/orders/", payload);
  return data;
}

export async function updateOrder(
  id: number,
  payload: Partial<OrderCreatePayload>
): Promise<Order> {
  const { data } = await api.put<Order>(`/orders/${id}`, payload);
  return data;
}

export async function deleteOrder(id: number): Promise<void> {
  await api.delete(`/orders/${id}`);
}

export async function cancelOrder(id: number): Promise<Order> {
  const { data } = await api.post<Order>(`/orders/${id}/cancel`);
  return data;
}

export async function confirmOrder(id: number, confirmedBy: string): Promise<Order> {
  const { data } = await api.post<Order>(`/orders/${id}/confirm`, {
    confirmed_by: confirmedBy,
  });
  return data;
}
