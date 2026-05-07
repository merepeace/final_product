import {
  Box,
  Card,
  CardContent,
  Chip,
  Divider,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import ListAltIcon from "@mui/icons-material/ListAlt";
import PrecisionManufacturingIcon from "@mui/icons-material/PrecisionManufacturing";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import PinDropIcon from "@mui/icons-material/PinDrop";
import PageHeader from "../components/PageHeader";
import StatusChip from "../components/StatusChip";
import { listOrders } from "../api/orders";
import { listAGVs } from "../api/agvs";
import { listProducts } from "../api/products";
import { listZones } from "../api/zones";
import type { OrderStatus } from "../types";

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  hint?: string;
}

function StatCard({ icon, label, value, hint }: StatCardProps) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack direction="row" spacing={2} alignItems="center">
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2,
              bgcolor: "primary.light",
              color: "primary.contrastText",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {icon}
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h5" fontWeight={600}>
              {value}
            </Typography>
            {hint ? (
              <Typography variant="caption" color="text.secondary">
                {hint}
              </Typography>
            ) : null}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const ordersQuery = useQuery({
    queryKey: ["orders"],
    queryFn: listOrders,
    refetchInterval: 5000,
  });
  const agvsQuery = useQuery({
    queryKey: ["agvs"],
    queryFn: listAGVs,
    refetchInterval: 5000,
  });
  const productsQuery = useQuery({
    queryKey: ["products"],
    queryFn: listProducts,
  });
  const zonesQuery = useQuery({
    queryKey: ["zones"],
    queryFn: listZones,
    refetchInterval: 5000,
  });

  const orders = ordersQuery.data ?? [];
  const agvs = agvsQuery.data ?? [];
  const products = productsQuery.data ?? [];
  const zones = zonesQuery.data ?? [];

  const statusCounts: Record<OrderStatus, number> = {
    pending: 0,
    assigned: 0,
    delivering: 0,
    done: 0,
    cancelled: 0,
  };
  for (const order of orders) {
    statusCounts[order.status] = (statusCounts[order.status] ?? 0) + 1;
  }

  const idleAgvs = agvs.filter((a) => a.status === "idle").length;
  const busyAgvs = agvs.filter((a) => a.status === "busy").length;

  const lowStock = products.filter(
    (p) => p.stock_quantity <= p.min_stock
  );

  const occupiedZones = zones.filter((z) => z.is_occupied).length;

  const isLoading =
    ordersQuery.isLoading ||
    agvsQuery.isLoading ||
    productsQuery.isLoading ||
    zonesQuery.isLoading;

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Live snapshot of warehouse operations"
      />
      {isLoading ? <LinearProgress sx={{ mb: 2 }} /> : null}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            icon={<ListAltIcon />}
            label="Total Orders"
            value={orders.length}
            hint={`${statusCounts.pending + statusCounts.assigned + statusCounts.delivering} active`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            icon={<PrecisionManufacturingIcon />}
            label="AGVs"
            value={`${idleAgvs} / ${agvs.length} idle`}
            hint={`${busyAgvs} busy`}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            icon={<Inventory2Icon />}
            label="Products"
            value={products.length}
            hint={
              lowStock.length > 0
                ? `${lowStock.length} below min stock`
                : "Stock levels OK"
            }
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            icon={<PinDropIcon />}
            label="Zones"
            value={zones.length}
            hint={`${occupiedZones} currently occupied`}
          />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Orders by Status
              </Typography>
              <Stack spacing={1.2}>
                {(
                  ["pending", "assigned", "delivering", "done", "cancelled"] as OrderStatus[]
                ).map((s) => (
                  <Stack
                    key={s}
                    direction="row"
                    alignItems="center"
                    spacing={2}
                  >
                    <Box sx={{ minWidth: 110 }}>
                      <StatusChip status={s} />
                    </Box>
                    <Box sx={{ flexGrow: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={
                          orders.length > 0
                            ? (statusCounts[s] / orders.length) * 100
                            : 0
                        }
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </Box>
                    <Box sx={{ minWidth: 32, textAlign: "right" }}>
                      {statusCounts[s]}
                    </Box>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Low Stock
              </Typography>
              {lowStock.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  All products are above their minimum stock level.
                </Typography>
              ) : (
                <Stack spacing={1} divider={<Divider flexItem />}>
                  {lowStock.map((p) => (
                    <Stack
                      key={p.id}
                      direction="row"
                      justifyContent="space-between"
                      alignItems="center"
                    >
                      <Box>
                        <Typography variant="body2" fontWeight={600}>
                          {p.productname}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {p.model} · {p.location}
                        </Typography>
                      </Box>
                      <Chip
                        size="small"
                        color="warning"
                        label={`${p.stock_quantity} / min ${p.min_stock}`}
                      />
                    </Stack>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
