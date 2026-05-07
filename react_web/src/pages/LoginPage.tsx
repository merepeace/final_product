import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import WarehouseIcon from "@mui/icons-material/Warehouse";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { extractApiError } from "../api/client";

interface LocationState {
  from?: string;
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as LocationState | null)?.from ?? "/";

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(extractApiError(err, "Login failed"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          "linear-gradient(135deg, #1976d2 0%, #5e35b1 100%)",
        p: 2,
      }}
    >
      <Card sx={{ width: 400, maxWidth: "100%" }}>
        <CardContent>
          <Stack alignItems="center" spacing={1} sx={{ mb: 3 }}>
            <WarehouseIcon color="primary" sx={{ fontSize: 48 }} />
            <Typography variant="h5" fontWeight={600}>
              WMS Console
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sign in to manage warehouse operations
            </Typography>
          </Stack>
          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                fullWidth
              />
              <TextField
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                fullWidth
              />
              {error ? <Alert severity="error">{error}</Alert> : null}
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={submitting}
                startIcon={
                  submitting ? <CircularProgress size={18} /> : null
                }
              >
                {submitting ? "Signing in..." : "Sign In"}
              </Button>
              <Typography
                variant="caption"
                color="text.secondary"
                textAlign="center"
              >
                Default credentials: admin / admin
              </Typography>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
