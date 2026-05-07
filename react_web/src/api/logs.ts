import { api } from "./client";
import type { SystemLog } from "../types";

export async function listLogs(limit = 100, source?: string): Promise<SystemLog[]> {
  const params: Record<string, string | number> = { limit };
  if (source) params.source = source;
  const { data } = await api.get<SystemLog[]>("/logs/", { params });
  return data;
}
