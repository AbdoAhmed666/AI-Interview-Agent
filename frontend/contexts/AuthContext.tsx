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
      if (!getToken()) {
        setLoading(false);
        return;
      }

      const currentUser =
        await getCurrentUser();

      setUser(currentUser);
    } catch {
      removeToken();
    } finally {
      setLoading(false);
    }
  }

  async function login(
    data: LoginRequest
  ) {
    const token =
      await loginService(data);

    saveToken(token.access_token);

    const currentUser =
      await getCurrentUser();

    setUser(currentUser);
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