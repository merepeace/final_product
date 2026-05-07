import { api } from "./client";
import type { AGV, AGVUpdatePayload } from "../types";

export async function listAGVs(): Promise<AGV[]> {
  const { data } = await api.get<AGV[]>("/agvs/");
  return data;
}

export async function updateAGV(id: number, payload: AGVUpdatePayload): Promise<AGV> {
  const { data } = await api.put<AGV>(`/agvs/${id}`, payload);
  return data;
}

export async function createAGV(name: string): Promise<AGV> {
  const { data } = await api.post<AGV>("/agvs/", { name });
  return data;
}

export async function deleteAGV(id: number): Promise<void> {
  await api.delete(`/agvs/${id}`);
}
