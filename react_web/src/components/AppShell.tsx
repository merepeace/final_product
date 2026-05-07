import {
  AppBar,
  Avatar,
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import LogoutIcon from "@mui/icons-material/Logout";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ListAltIcon from "@mui/icons-material/ListAlt";
import Inventory2Icon from "@mui/icons-material/Inventory2";
import PinDropIcon from "@mui/icons-material/PinDrop";
import PrecisionManufacturingIcon from "@mui/icons-material/PrecisionManufacturing";
import HistoryIcon from "@mui/icons-material/History";
import WarehouseIcon from "@mui/icons-material/Warehouse";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const DRAWER_WIDTH = 240;

const NAV = [
  { to: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { to: "/orders", label: "Orders", icon: <ListAltIcon /> },
  { to: "/products", label: "Products", icon: <Inventory2Icon /> },
  { to: "/zones", label: "Zones", icon: <PinDropIcon /> },
  { to: "/agvs", label: "AGVs", icon: <PrecisionManufacturingIcon /> },
  { to: "/logs", label: "Logs", icon: <HistoryIcon /> },
];

export default function AppShell() {
  const { username, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  function isActive(to: string) {
    if (to === "/") return location.pathname === "/";
    return location.pathname.startsWith(to);
  }

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${DRAWER_WIDTH}px)`,
          ml: `${DRAWER_WIDTH}px`,
        }}
      >
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Warehouse Management System
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Avatar sx={{ width: 32, height: 32, bgcolor: "secondary.main" }}>
              {(username ?? "?").slice(0, 1).toUpperCase()}
            </Avatar>
            <Typography variant="body2">{username ?? "guest"}</Typography>
            <Tooltip title="Sign out">
              <IconButton color="inherit" onClick={handleLogout}>
                <LogoutIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: DRAWER_WIDTH,
            boxSizing: "border-box",
          },
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <WarehouseIcon color="primary" />
          <Typography variant="h6" fontWeight={600}>
            WMS
          </Typography>
        </Toolbar>
        <Divider />
        <List>
          {NAV.map((item) => (
            <ListItemButton
              key={item.to}
              selected={isActive(item.to)}
              onClick={() => navigate(item.to)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: "background.default",
          p: 3,
          mt: 8,
          minHeight: "calc(100vh - 64px)",
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
