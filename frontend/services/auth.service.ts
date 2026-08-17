import api from "@/lib/axios";

export async function register(data: { name: string; email: string; password: string }) {
  const resp = await api.post("/register", data);
  return resp.data;
}

export async function login(data: { email: string; password: string }) {
  const resp = await api.post("/login", data);
  return resp.data;
}

export async function getCurrentUser() {
  const resp = await api.get("/me");
  return resp.data;
}