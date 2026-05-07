import { useState } from "react";
import {
  Box,
  Chip,
  MenuItem,
  Stack,
  TextField,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef } from "@mui/x-data-grid";
import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import ExportCsvButton from "../components/ExportCsvButton";
import type { CsvColumn } from "../utils/csv";
import { listLogs } from "../api/logs";
import type { SystemLog } from "../types";

const LOG_CSV_COLUMNS: CsvColumn<SystemLog>[] = [
  { header: "ID", accessor: (l) => l.id },
  { header: "Timestamp", accessor: (l) => l.timestamp },
  { header: "Level", accessor: (l) => l.level },
  { header: "Source", accessor: (l) => l.source },
  { header: "Message", accessor: (l) => l.message },
];

const LEVEL_COLOR: Record<string, "default" | "info" | "warning" | "error" | "success"> = {
  INFO: "info",
  WARN: "warning",
  ERROR: "error",
  SUCCESS: "success",
};

export default function LogsPage() {
  const [limit, setLimit] = useState(100);
  const [source, setSource] = useState<string>("");

  const query = useQuery({
    queryKey: ["logs", limit, source],
    queryFn: () => listLogs(limit, source || undefined),
    refetchInterval: 5000,
  });

  const columns: GridColDef<SystemLog>[] = [
    { field: "id", headerName: "ID", width: 70 },
    {
      field: "timestamp",
      headerName: "Timestamp",
      width: 200,
      valueFormatter: (value: string) =>
        value ? new Date(value).toLocaleString() : "",
    },
    {
      field: "level",
      headerName: "Level",
      width: 100,
      renderCell: (p) => (
        <Chip
          size="small"
          label={p.row.level}
          color={LEVEL_COLOR[p.row.level] ?? "default"}
        />
      ),
    },
    { field: "source", headerName: "Source", width: 130 },
    { field: "message", headerName: "Message", flex: 1, minWidth: 320 },
  ];

  return (
    <Box>
      <PageHeader
        title="System Logs"
        subtitle="Live feed - refreshes every 5s"
        actions={
          <ExportCsvButton<SystemLog>
            basename="logs"
            rows={query.data ?? []}
            columns={LOG_CSV_COLUMNS}
          />
        }
      />
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        <TextField
          select
          label="Limit"
          size="small"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          sx={{ width: 120 }}
        >
          {[25, 50, 100, 250, 500].map((n) => (
            <MenuItem key={n} value={n}>
              {n}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Source filter"
          size="small"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="API, AGV-1, SIMULATOR..."
          sx={{ width: 220 }}
        />
      </Stack>
      <Box sx={{ height: 600, width: "100%", bgcolor: "background.paper" }}>
        <DataGrid<SystemLog>
          rows={query.data ?? []}
          columns={columns}
          loading={query.isLoading}
          disableRowSelectionOnClick
          pageSizeOptions={[25, 50, 100]}
          initialState={{
            pagination: { paginationModel: { pageSize: 50, page: 0 } },
          }}
        />
      </Box>
    </Box>
  );
}
