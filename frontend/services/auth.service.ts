import api from "@/lib/axios";
import {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
} from "@/types/auth";

export async function register(data: RegisterRequest) {
  const response = await api.post("/register", data);

  return response.data;
}

export async function login(
  data: LoginRequest
): Promise<LoginResponse> {
  const response = await api.post("/login", data);

  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get("/me");

  return response.data;
}