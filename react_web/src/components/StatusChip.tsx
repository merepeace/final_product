import { Chip } from "@mui/material";
import type { OrderStatus } from "../types";

const COLOR_MAP: Record<OrderStatus, "default" | "warning" | "info" | "primary" | "success" | "error"> = {
  pending: "warning",
  assigned: "info",
  delivering: "primary",
  done: "success",
  cancelled: "error",
};

export default function StatusChip({ status }: { status: OrderStatus }) {
  return (
    <Chip
      label={status.toUpperCase()}
      color={COLOR_MAP[status] ?? "default"}
      size="small"
      variant="filled"
    />
  );
}
