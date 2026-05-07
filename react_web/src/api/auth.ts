import { api } from "./client";
import type { LoginPayload, TokenResponse } from "../types";

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function getMe(): Promise<{ username: string }> {
  const { data } = await api.get<{ username: string }>("/auth/me");
  return data;
}
