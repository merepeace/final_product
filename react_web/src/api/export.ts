import { api } from "./client";

export interface ExportSnapshotResponse {
  ok: boolean;
  directory: string;
  files: string[];
}

export async function postExportSnapshot(): Promise<ExportSnapshotResponse> {
  const { data } = await api.post<ExportSnapshotResponse>("/export/snapshot");
  return data;
}
