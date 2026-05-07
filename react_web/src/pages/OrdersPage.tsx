import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { DataGrid } from "@mui/x-data-grid";
import type { GridColDef } from "@mui/x-data-grid";
import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "react-toastify";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import ExportCsvButton from "../components/ExportCsvButton";
import type { CsvColumn } from "../utils/csv";
import {
  cancelOrder,
  confirmOrder,
  createOrder,
  listOrders,
} from "../api/orders";
import { listProducts } from "../api/products";
import { listZones } from "../api/zones";
import { extractApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { Order } from "../types";

const schema = z.object({
  order_name: z.string().min(1, "Required"),
  product: z.string().min(1, "Required"),
  qty: z.number().int().gt(0, "Must be > 0"),
  priority: z.number().int().min(1).max(5),
  from_location: z.string().min(1, "Required"),
  to_location: z.string().min(1, "Required"),
});

type FormValues = z.infer<typeof schema>;

const ORDER_CSV_COLUMNS: CsvColumn<Order>[] = [
  { header: "ID", accessor: (o) => o.id },
  { header: "Order Name", accessor: (o) => o.order_name },
  { header: "Product", accessor: (o) => o.product },
  { header: "Quantity", accessor: (o) => o.qty },
  { header: "Status", accessor: (o) => o.status },
  { header: "AGV", accessor: (o) => o.agv ?? "" },
  { header: "Priority", accessor: (o) => o.priority },
  { header: "From Location", accessor: (o) => o.from_location },
  { header: "To Location", accessor: (o) => o.to_location },
  { header: "Order Time", accessor: (o) => o.order_time },
  { header: "Completed At", accessor: (o) => o.completed_timestamp ?? "" },
  { header: "Confirmed By", accessor: (o) => o.confirmed_by ?? "" },
];

const DEFAULTS: FormValues = {
  order_name: "",
  product: "",
  qty: 1,
  priority: 3,
  from_location: "Warehouse",
  to_location: "Zone A",
};

export default function OrdersPage() {
  const qc = useQueryClient();
  const { username } = useAuth();
  const [confirmDialog, setConfirmDialog] = useState<Order | null>(null);
  const [confirmedBy, setConfirmedBy] = useState("");

  const ordersQuery = useQuery({
    queryKey: ["orders"],
    queryFn: listOrders,
    refetchInterval: 5000,
  });
  const productsQuery = useQuery({ queryKey: ["products"], queryFn: listProducts });
  const zonesQuery = useQuery({ queryKey: ["zones"], queryFn: listZones });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULTS,
  });

  const createMut = useMutation({
    mutationFn: createOrder,
    onSuccess: () => {
      toast.success("Order created");
      qc.invalidateQueries({ queryKey: ["orders"] });
      form.reset(DEFAULTS);
    },
    onError: (err) => toast.error(extractApiError(err, "Create failed")),
  });

  const cancelMut = useMutation({
    mutationFn: (id: number) => cancelOrder(id),
    onSuccess: () => {
      toast.success("Order cancelled");
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: (err) => toast.error(extractApiError(err, "Cancel failed")),
  });

  const confirmMut = useMutation({
    mutationFn: ({ id, by }: { id: number; by: string }) => confirmOrder(id, by),
    onSuccess: () => {
      toast.success("Delivery confirmed");
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["products"] });
      setConfirmDialog(null);
      setConfirmedBy("");
    },
    onError: (err) => toast.error(extractApiError(err, "Confirm failed")),
  });

  function onSubmit(values: FormValues) {
    if (values.from_location === values.to_location) {
      form.setError("to_location", {
        type: "manual",
        message: "From and To must differ",
      });
      return;
    }
    createMut.mutate(values);
  }

  const products = productsQuery.data ?? [];
  const zones = zonesQuery.data ?? [];

  const columns: GridColDef<Order>[] = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "order_name", headerName: "Name", flex: 1.5, minWidth: 140 },
    { field: "product", headerName: "Product", flex: 1.5, minWidth: 140 },
    { field: "qty", headerName: "Qty", width: 70, type: "number" },
    {
      field: "status",
      headerName: "Status",
      width: 130,
      renderCell: (p) => <StatusChip status={p.row.status} />,
    },
    { field: "agv", headerName: "AGV", width: 90 },
    { field: "priority", headerName: "P", width: 60, type: "number" },
    { field: "from_location", headerName: "From", width: 110 },
    { field: "to_location", headerName: "To", width: 110 },
    {
      field: "order_time",
      headerName: "Created",
      width: 170,
      valueFormatter: (value: string) =>
        value ? new Date(value).toLocaleString() : "",
    },
    {
      field: "actions",
      headerName: "",
      width: 120,
      sortable: false,
      filterable: false,
      renderCell: (params) => {
        const order = params.row;
        const canCancel = !["done", "cancelled"].includes(order.status);
        const canConfirm = order.status === "delivering";
        return (
          <Stack direction="row">
            <Tooltip title="Confirm Delivery">
              <span>
                <IconButton
                  size="small"
                  color="success"
                  disabled={!canConfirm}
                  onClick={() => {
                    setConfirmDialog(order);
                    setConfirmedBy(username ?? "");
                  }}
                >
                  <CheckCircleIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title="Cancel Order">
              <span>
                <IconButton
                  size="small"
                  color="error"
                  disabled={!canCancel}
                  onClick={() => {
                    if (confirm(`Cancel order #${order.id}?`)) {
                      cancelMut.mutate(order.id);
                    }
                  }}
                >
                  <CancelIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Stack>
        );
      },
    },
  ];

  return (
    <Box>
      <PageHeader
        title="Orders"
        subtitle="Auto-refreshing every 5 seconds"
        actions={
          <>
            <ExportCsvButton<Order>
              basename="orders"
              rows={ordersQuery.data ?? []}
              columns={ORDER_CSV_COLUMNS}
            />
            <Button
              startIcon={<RefreshIcon />}
              onClick={() => qc.invalidateQueries({ queryKey: ["orders"] })}
            >
              Refresh
            </Button>
          </>
        }
      />

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  label="Order Name"
                  fullWidth
                  size="small"
                  {...form.register("order_name")}
                  error={!!form.formState.errors.order_name}
                  helperText={form.formState.errors.order_name?.message}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  select
                  label="Product"
                  fullWidth
                  size="small"
                  value={form.watch("product") ?? ""}
                  onChange={(e) =>
                    form.setValue("product", e.target.value, {
                      shouldValidate: true,
                    })
                  }
                  error={!!form.formState.errors.product}
                  helperText={
                    form.formState.errors.product?.message ??
                    (products.length === 0 ? "Create a product first" : undefined)
                  }
                >
                  {products.map((p) => (
                    <MenuItem key={p.id} value={p.productname}>
                      {p.productname} (stock: {p.stock_quantity})
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 6, md: 2 }}>
                <TextField
                  label="Qty"
                  type="number"
                  fullWidth
                  size="small"
                  {...form.register("qty", { valueAsNumber: true })}
                  error={!!form.formState.errors.qty}
                  helperText={form.formState.errors.qty?.message}
                />
              </Grid>
              <Grid size={{ xs: 6, md: 2 }}>
                <TextField
                  select
                  label="Priority"
                  fullWidth
                  size="small"
                  value={form.watch("priority") ?? 3}
                  onChange={(e) =>
                    form.setValue("priority", Number(e.target.value), {
                      shouldValidate: true,
                    })
                  }
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <MenuItem key={n} value={n}>
                      {n}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 6, md: 4 }}>
                <TextField
                  select
                  label="From Location"
                  fullWidth
                  size="small"
                  value={form.watch("from_location") ?? ""}
                  onChange={(e) =>
                    form.setValue("from_location", e.target.value, {
                      shouldValidate: true,
                    })
                  }
                >
                  {zones.map((z) => (
                    <MenuItem key={z.id} value={z.name}>
                      {z.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 6, md: 4 }}>
                <TextField
                  select
                  label="To Location"
                  fullWidth
                  size="small"
                  value={form.watch("to_location") ?? ""}
                  onChange={(e) =>
                    form.setValue("to_location", e.target.value, {
                      shouldValidate: true,
                    })
                  }
                  error={!!form.formState.errors.to_location}
                  helperText={form.formState.errors.to_location?.message}
                >
                  {zones.map((z) => (
                    <MenuItem key={z.id} value={z.name}>
                      {z.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }} sx={{ display: "flex", alignItems: "center" }}>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={createMut.isPending}
                  fullWidth
                >
                  {createMut.isPending ? "Creating..." : "Create Order"}
                </Button>
              </Grid>
            </Grid>
          </form>
          {ordersQuery.isError ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              {extractApiError(ordersQuery.error, "Failed to load orders")}
            </Alert>
          ) : null}
        </CardContent>
      </Card>

      <Box sx={{ height: 600, width: "100%", bgcolor: "background.paper" }}>
        <DataGrid<Order>
          rows={ordersQuery.data ?? []}
          columns={columns}
          loading={ordersQuery.isLoading}
          disableRowSelectionOnClick
          getRowId={(row) => row.id}
          initialState={{
            pagination: { paginationModel: { pageSize: 25, page: 0 } },
            sorting: { sortModel: [{ field: "id", sort: "desc" }] },
          }}
          pageSizeOptions={[10, 25, 50]}
        />
      </Box>

      <Dialog
        open={!!confirmDialog}
        onClose={() => setConfirmDialog(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Confirm Delivery</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Box>
              Confirm delivery for order #{confirmDialog?.id} (
              {confirmDialog?.order_name})?
            </Box>
            <TextField
              label="Confirmed by"
              value={confirmedBy}
              onChange={(e) => setConfirmedBy(e.target.value)}
              autoFocus
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            disabled={!confirmedBy.trim() || confirmMut.isPending}
            onClick={() =>
              confirmDialog &&
              confirmMut.mutate({ id: confirmDialog.id, by: confirmedBy.trim() })
            }
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
