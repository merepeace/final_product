import { api } from "./client";
import type { Zone, ZoneCreatePayload } from "../types";

export async function listZones(): Promise<Zone[]> {
  const { data } = await api.get<Zone[]>("/zones/");
  return data;
}

export async function createZone(payload: ZoneCreatePayload): Promise<Zone> {
  const { data } = await api.post<Zone>("/zones/", payload);
  return data;
}

export async function updateZone(
  id: number,
  payload: Partial<ZoneCreatePayload>
): Promise<Zone> {
  const { data } = await api.put<Zone>(`/zones/${id}`, payload);
  return data;
}

export async function deleteZone(id: number): Promise<void> {
  await api.delete(`/zones/${id}`);
}
