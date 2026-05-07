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
  MenuItem,
  Stack,
  Switch,
  TextField,
  Tooltip,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef } from "@mui/x-data-grid";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "react-toastify";
import PageHeader from "../components/PageHeader";
import ExportCsvButton from "../components/ExportCsvButton";
import type { CsvColumn } from "../utils/csv";
import {
  createZone,
  deleteZone,
  listZones,
  updateZone,
} from "../api/zones";
import { extractApiError } from "../api/client";
import type { Zone, ZoneCreatePayload } from "../types";

const schema = z.object({
  name: z.string().min(1, "Required"),
  zone_type: z.string().min(1, "Required"),
  is_active: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const ZONE_CSV_COLUMNS: CsvColumn<Zone>[] = [
  { header: "ID", accessor: (z) => z.id },
  { header: "Name", accessor: (z) => z.name },
  { header: "Type", accessor: (z) => z.zone_type },
  { header: "Active", accessor: (z) => z.is_active },
  { header: "Occupied", accessor: (z) => z.is_occupied },
];

const EMPTY: FormValues = {
  name: "",
  zone_type: "destination",
  is_active: true,
};

export default function ZonesPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<Zone | null>(null);
  const [open, setOpen] = useState(false);

  const zonesQuery = useQuery({
    queryKey: ["zones"],
    queryFn: listZones,
    refetchInterval: 5000,
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  const createMut = useMutation({
    mutationFn: (payload: ZoneCreatePayload) => createZone(payload),
    onSuccess: () => {
      toast.success("Zone created");
      qc.invalidateQueries({ queryKey: ["zones"] });
      handleClose();
    },
    onError: (err) => toast.error(extractApiError(err, "Create failed")),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ZoneCreatePayload }) =>
      updateZone(id, payload),
    onSuccess: () => {
      toast.success("Zone updated");
      qc.invalidateQueries({ queryKey: ["zones"] });
      handleClose();
    },
    onError: (err) => toast.error(extractApiError(err, "Update failed")),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteZone(id),
    onSuccess: () => {
      toast.success("Zone deleted");
      qc.invalidateQueries({ queryKey: ["zones"] });
    },
    onError: (err) => toast.error(extractApiError(err, "Delete failed")),
  });

  function handleOpen(zone?: Zone) {
    if (zone) {
      setEditing(zone);
      form.reset({
        name: zone.name,
        zone_type: zone.zone_type,
        is_active: zone.is_active,
      });
    } else {
      setEditing(null);
      form.reset(EMPTY);
    }
    setOpen(true);
  }

  function handleClose() {
    setOpen(false);
    setEditing(null);
    form.reset(EMPTY);
  }

  function onSubmit(values: FormValues) {
    if (editing) {
      updateMut.mutate({ id: editing.id, payload: values });
    } else {
      createMut.mutate(values);
    }
  }

  const columns: GridColDef<Zone>[] = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "name", headerName: "Name", flex: 1, minWidth: 140 },
    { field: "zone_type", headerName: "Type", width: 130 },
    {
      field: "is_active",
      headerName: "Active",
      width: 110,
      renderCell: (p) => (
        <Chip
          label={p.row.is_active ? "Active" : "Inactive"}
          color={p.row.is_active ? "success" : "default"}
          size="small"
        />
      ),
    },
    {
      field: "is_occupied",
      headerName: "Occupancy",
      width: 130,
      renderCell: (p) => (
        <Chip
          label={p.row.is_occupied ? "Occupied" : "Vacant"}
          color={p.row.is_occupied ? "warning" : "success"}
          size="small"
          variant="outlined"
        />
      ),
    },
    {
      field: "actions",
      headerName: "",
      width: 110,
      sortable: false,
      filterable: false,
      renderCell: (params) => (
        <Stack direction="row">
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => handleOpen(params.row)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton
              size="small"
              color="error"
              onClick={() => {
                if (confirm(`Delete zone '${params.row.name}'?`)) {
                  deleteMut.mutate(params.row.id);
                }
              }}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      ),
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Zones"
        subtitle="Storage and destination locations"
        actions={
          <>
            <ExportCsvButton<Zone>
              basename="zones"
              rows={zonesQuery.data ?? []}
              columns={ZONE_CSV_COLUMNS}
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpen()}
            >
              New Zone
            </Button>
          </>
        }
      />
      <Box sx={{ height: 600, width: "100%", bgcolor: "background.paper" }}>
        <DataGrid<Zone>
          rows={zonesQuery.data ?? []}
          columns={columns}
          loading={zonesQuery.isLoading}
          disableRowSelectionOnClick
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25, page: 0 } },
          }}
        />
      </Box>

      <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogTitle>{editing ? "Edit Zone" : "Create Zone"}</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Name"
                {...form.register("name")}
                error={!!form.formState.errors.name}
                helperText={form.formState.errors.name?.message}
                fullWidth
              />
              <TextField
                select
                label="Type"
                value={form.watch("zone_type")}
                onChange={(e) =>
                  form.setValue("zone_type", e.target.value, {
                    shouldValidate: true,
                  })
                }
                fullWidth
              >
                <MenuItem value="source">Source</MenuItem>
                <MenuItem value="destination">Destination</MenuItem>
              </TextField>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Switch
                  checked={form.watch("is_active")}
                  onChange={(_, v) => form.setValue("is_active", v)}
                />
                <Box>{form.watch("is_active") ? "Active" : "Inactive"}</Box>
              </Stack>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMut.isPending || updateMut.isPending}
            >
              {editing ? "Save" : "Create"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
