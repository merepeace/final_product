import { useState } from "react";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  TextField,
  Tooltip,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef } from "@mui/x-data-grid";
import EditIcon from "@mui/icons-material/Edit";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import PageHeader from "../components/PageHeader";
import ExportCsvButton from "../components/ExportCsvButton";
import type { CsvColumn } from "../utils/csv";
import { listAGVs, updateAGV } from "../api/agvs";
import { extractApiError } from "../api/client";
import type { AGV } from "../types";

const AGV_CSV_COLUMNS: CsvColumn<AGV>[] = [
  { header: "ID", accessor: (a) => a.id },
  { header: "Name", accessor: (a) => a.name },
  { header: "Status", accessor: (a) => a.status },
  { header: "Current Order ID", accessor: (a) => a.current_order_id ?? "" },
  { header: "Last Active", accessor: (a) => a.last_active ?? "" },
];

export default function AgvsPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<AGV | null>(null);
  const [name, setName] = useState("");

  const agvsQuery = useQuery({
    queryKey: ["agvs"],
    queryFn: listAGVs,
    refetchInterval: 5000,
  });

  const renameMut = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      updateAGV(id, { name }),
    onSuccess: () => {
      toast.success("AGV updated");
      qc.invalidateQueries({ queryKey: ["agvs"] });
      setEditing(null);
      setName("");
    },
    onError: (err) => toast.error(extractApiError(err, "Update failed")),
  });

  const columns: GridColDef<AGV>[] = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "name", headerName: "Name", flex: 1, minWidth: 140 },
    {
      field: "status",
      headerName: "Status",
      width: 130,
      renderCell: (p) => (
        <Chip
          label={p.row.status.toUpperCase()}
          color={
            p.row.status === "idle"
              ? "success"
              : p.row.status === "busy"
              ? "warning"
              : "default"
          }
          size="small"
        />
      ),
    },
    {
      field: "current_order_id",
      headerName: "Current Order",
      width: 140,
      renderCell: (p) =>
        p.row.current_order_id ? `#${p.row.current_order_id}` : "—",
    },
    {
      field: "last_active",
      headerName: "Last Active",
      width: 200,
      valueFormatter: (value: string | null) =>
        value ? new Date(value).toLocaleString() : "—",
    },
    {
      field: "actions",
      headerName: "",
      width: 80,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Tooltip title="Rename">
          <IconButton
            size="small"
            onClick={() => {
              setEditing(params.row);
              setName(params.row.name);
            }}
          >
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="AGVs"
        subtitle="Automated Guided Vehicles - status updates live"
        actions={
          <ExportCsvButton<AGV>
            basename="agvs"
            rows={agvsQuery.data ?? []}
            columns={AGV_CSV_COLUMNS}
          />
        }
      />
      <Box sx={{ height: 500, width: "100%", bgcolor: "background.paper" }}>
        <DataGrid<AGV>
          rows={agvsQuery.data ?? []}
          columns={columns}
          loading={agvsQuery.isLoading}
          disableRowSelectionOnClick
        />
      </Box>

      <Dialog
        open={!!editing}
        onClose={() => setEditing(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Rename AGV #{editing?.id}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
              autoFocus
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditing(null)}>Cancel</Button>
          <Button
            variant="contained"
            disabled={!name.trim() || renameMut.isPending}
            onClick={() =>
              editing && renameMut.mutate({ id: editing.id, name: name.trim() })
            }
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
