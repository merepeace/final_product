import { useState } from "react";
import {
  Box,
  Button,
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
  createProduct,
  deleteProduct,
  listProducts,
  updateProduct,
} from "../api/products";
import { listZones } from "../api/zones";
import { extractApiError } from "../api/client";
import type { Product, ProductCreatePayload } from "../types";

const schema = z.object({
  productname: z.string().min(1, "Required"),
  model: z.string().min(1, "Required"),
  color: z.string().min(1, "Required"),
  stock_quantity: z.number().int().min(0, "Must be >= 0"),
  price_usd: z.number().gt(0, "Must be > 0"),
  location: z.string().min(1, "Required"),
  min_stock: z.number().int().min(0, "Must be >= 0"),
});

type FormValues = z.infer<typeof schema>;

const PRODUCT_CSV_COLUMNS: CsvColumn<Product>[] = [
  { header: "ID", accessor: (p) => p.id },
  { header: "Name", accessor: (p) => p.productname },
  { header: "Model", accessor: (p) => p.model },
  { header: "Color", accessor: (p) => p.color },
  { header: "Stock Quantity", accessor: (p) => p.stock_quantity },
  { header: "Min Stock", accessor: (p) => p.min_stock },
  { header: "Price (USD)", accessor: (p) => p.price_usd },
  { header: "Location", accessor: (p) => p.location },
];

const EMPTY: FormValues = {
  productname: "",
  model: "",
  color: "",
  stock_quantity: 0,
  price_usd: 1,
  location: "Warehouse",
  min_stock: 0,
};

export default function ProductsPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<Product | null>(null);
  const [open, setOpen] = useState(false);

  const productsQuery = useQuery({
    queryKey: ["products"],
    queryFn: listProducts,
  });
  const zonesQuery = useQuery({ queryKey: ["zones"], queryFn: listZones });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: EMPTY,
  });

  const createMut = useMutation({
    mutationFn: (payload: ProductCreatePayload) => createProduct(payload),
    onSuccess: () => {
      toast.success("Product created");
      qc.invalidateQueries({ queryKey: ["products"] });
      handleClose();
    },
    onError: (err) => toast.error(extractApiError(err, "Create failed")),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ProductCreatePayload }) =>
      updateProduct(id, payload),
    onSuccess: () => {
      toast.success("Product updated");
      qc.invalidateQueries({ queryKey: ["products"] });
      handleClose();
    },
    onError: (err) => toast.error(extractApiError(err, "Update failed")),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteProduct(id),
    onSuccess: () => {
      toast.success("Product deleted");
      qc.invalidateQueries({ queryKey: ["products"] });
    },
    onError: (err) => toast.error(extractApiError(err, "Delete failed")),
  });

  function handleOpen(product?: Product) {
    if (product) {
      setEditing(product);
      form.reset({
        productname: product.productname,
        model: product.model,
        color: product.color,
        stock_quantity: product.stock_quantity,
        price_usd: product.price_usd,
        location: product.location,
        min_stock: product.min_stock,
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

  const columns: GridColDef<Product>[] = [
    { field: "productname", headerName: "Name", flex: 1.5, minWidth: 160 },
    { field: "model", headerName: "Model", flex: 1, minWidth: 120 },
    { field: "color", headerName: "Color", width: 100 },
    {
      field: "stock_quantity",
      headerName: "Stock",
      width: 100,
      type: "number",
    },
    {
      field: "min_stock",
      headerName: "Min",
      width: 80,
      type: "number",
    },
    {
      field: "price_usd",
      headerName: "Price (USD)",
      width: 120,
      type: "number",
      valueFormatter: (value: number) => `$${value.toFixed(2)}`,
    },
    { field: "location", headerName: "Location", width: 130 },
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
                if (confirm(`Delete '${params.row.productname}'?`)) {
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

  const zoneOptions = zonesQuery.data ?? [];

  return (
    <Box>
      <PageHeader
        title="Products"
        subtitle="Inventory available to ship"
        actions={
          <>
            <ExportCsvButton<Product>
              basename="products"
              rows={productsQuery.data ?? []}
              columns={PRODUCT_CSV_COLUMNS}
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpen()}
            >
              New Product
            </Button>
          </>
        }
      />
      <Box sx={{ height: 600, width: "100%", bgcolor: "background.paper" }}>
        <DataGrid<Product>
          rows={productsQuery.data ?? []}
          columns={columns}
          loading={productsQuery.isLoading}
          disableRowSelectionOnClick
          initialState={{
            pagination: { paginationModel: { pageSize: 25, page: 0 } },
          }}
          pageSizeOptions={[10, 25, 50]}
        />
      </Box>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogTitle>
            {editing ? "Edit Product" : "Create Product"}
          </DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                label="Product Name"
                {...form.register("productname")}
                error={!!form.formState.errors.productname}
                helperText={form.formState.errors.productname?.message}
                fullWidth
              />
              <Stack direction="row" spacing={2}>
                <TextField
                  label="Model"
                  {...form.register("model")}
                  error={!!form.formState.errors.model}
                  helperText={form.formState.errors.model?.message}
                  fullWidth
                />
                <TextField
                  label="Color"
                  {...form.register("color")}
                  error={!!form.formState.errors.color}
                  helperText={form.formState.errors.color?.message}
                  fullWidth
                />
              </Stack>
              <Stack direction="row" spacing={2}>
                <TextField
                  label="Stock"
                  type="number"
                  {...form.register("stock_quantity", { valueAsNumber: true })}
                  error={!!form.formState.errors.stock_quantity}
                  helperText={form.formState.errors.stock_quantity?.message}
                  fullWidth
                />
                <TextField
                  label="Min Stock"
                  type="number"
                  {...form.register("min_stock", { valueAsNumber: true })}
                  error={!!form.formState.errors.min_stock}
                  helperText={form.formState.errors.min_stock?.message}
                  fullWidth
                />
                <TextField
                  label="Price (USD)"
                  type="number"
                  inputProps={{ step: "0.01" }}
                  {...form.register("price_usd", { valueAsNumber: true })}
                  error={!!form.formState.errors.price_usd}
                  helperText={form.formState.errors.price_usd?.message}
                  fullWidth
                />
              </Stack>
              <TextField
                select
                label="Location"
                value={form.watch("location") ?? ""}
                onChange={(e) =>
                  form.setValue("location", e.target.value, {
                    shouldValidate: true,
                  })
                }
                error={!!form.formState.errors.location}
                helperText={form.formState.errors.location?.message}
                SelectProps={{ native: true }}
                fullWidth
              >
                <option value="">Select…</option>
                {zoneOptions.map((z) => (
                  <option key={z.id} value={z.name}>
                    {z.name}
                  </option>
                ))}
              </TextField>
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
