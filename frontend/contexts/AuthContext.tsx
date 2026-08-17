"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  getCurrentUser,
  login as loginService,
} from "@/services/auth.service";

import {
  LoginRequest,
  User,
} from "@/types/auth";

import {
  getToken,
  removeToken,
  saveToken,
} from "@/utils/token";

interface AuthContextType {
  user: User | null;

  loading: boolean;

  login: (
    data: LoginRequest
  ) => Promise<void>;

  logout: () => void;

  isAuthenticated: boolean;
}

const AuthContext =
  createContext<AuthContextType | null>(null);

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] =
    useState<User | null>(null);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  async function loadUser() {
    try {
      // Only attempt to load user if a token is present
      const token = getToken();
      if (token) {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } else {
        setUser(null);
      }
    } catch {
      removeToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function login(
    data: LoginRequest
  ) {
    const tokenResp = await loginService(data);
    const token = typeof tokenResp === "string" ? tokenResp : tokenResp?.access_token;
    if (token) {
      saveToken(token);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } else {
      throw new Error("Login failed: no token returned");
    }
  }

  function logout() {
    removeToken();

    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated:
          !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}
