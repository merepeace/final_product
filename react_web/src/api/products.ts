import { api } from "./client";
import type { Product, ProductCreatePayload } from "../types";

export async function listProducts(): Promise<Product[]> {
  const { data } = await api.get<Product[]>("/products/");
  return data;
}

export async function createProduct(payload: ProductCreatePayload): Promise<Product> {
  const { data } = await api.post<Product>("/products/", payload);
  return data;
}

export async function updateProduct(
  id: string,
  payload: ProductCreatePayload
): Promise<Product> {
  const { data } = await api.put<Product>(`/products/${id}`, payload);
  return data;
}

export async function deleteProduct(id: string): Promise<void> {
  await api.delete(`/products/${id}`);
}
