import { Chip } from "@mui/material";
import type { OrderStatus } from "../types";

const COLOR_MAP: Record<
  OrderStatus,
  "default" | "warning" | "info" | "primary" | "success" | "error" | "secondary"
> = {
  pending: "warning",
  validated: "info",
  assigned: "info",
  in_transit: "primary",
  delivered: "success",
  cancelled: "error",
  failed: "error",
};

const LABEL_MAP: Record<OrderStatus, string> = {
  pending: "PENDING",
  validated: "VALIDATED",
  assigned: "ASSIGNED",
  in_transit: "IN TRANSIT",
  delivered: "DELIVERED",
  cancelled: "CANCELLED",
  failed: "FAILED",
};

export default function StatusChip({ status }: { status: OrderStatus }) {
  return (
    <Chip
      label={LABEL_MAP[status] ?? String(status).toUpperCase()}
      color={COLOR_MAP[status] ?? "default"}
      size="small"
      variant="filled"
    />
  );
}
