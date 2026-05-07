import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { login as loginApi } from "../api/auth";
import { TOKEN_STORAGE_KEY } from "../api/client";

interface AuthContextValue {
  token: string | null;
  username: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const USERNAME_STORAGE_KEY = "wms.username";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY)
  );
  const [username, setUsername] = useState<string | null>(() =>
    localStorage.getItem(USERNAME_STORAGE_KEY)
  );

  useEffect(() => {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
  }, [token]);

  useEffect(() => {
    if (username) localStorage.setItem(USERNAME_STORAGE_KEY, username);
    else localStorage.removeItem(USERNAME_STORAGE_KEY);
  }, [username]);

  const login = useCallback(async (user: string, password: string) => {
    const data = await loginApi({ username: user, password });
    setToken(data.access_token);
    setUsername(user);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUsername(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      username,
      isAuthenticated: Boolean(token),
      login,
      logout,
    }),
    [token, username, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
