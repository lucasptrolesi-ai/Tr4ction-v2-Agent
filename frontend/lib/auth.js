"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

// Chaves do localStorage
const TOKEN_KEY = "tr4ction_token";
const USER_KEY = "tr4ction_user";

/**
 * Contexto de autenticação
 */
const AuthContext = createContext(null);

/**
 * Provider de autenticação
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Carrega dados do localStorage ao iniciar
  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  // Protege rotas baseado no role
  useEffect(() => {
    if (loading) return;

    const publicPaths = ["/", "/login", "/register"];
    const isPublicPath = publicPaths.includes(pathname);

    if (!user && !isPublicPath) {
      // Não autenticado tentando acessar rota protegida
      router.push("/login");
      return;
    }

    if (user) {
      // Verifica permissões de role
      if (pathname.startsWith("/admin") && user.role !== "admin") {
        router.push("/founder/dashboard");
        return;
      }

      if (pathname.startsWith("/founder") && user.role !== "founder") {
        router.push("/admin/dashboard");
        return;
      }
    }
  }, [user, loading, pathname, router]);

  /**
   * Realiza login
   */
  const login = useCallback(async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || "Erro ao fazer login");
    }

    const data = await res.json();
    
    // Salva no state e localStorage
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));

    // Redireciona baseado no role
    if (data.user.role === "admin") {
      router.push("/admin/dashboard");
    } else {
      router.push("/founder/dashboard");
    }

    return data.user;
  }, [router]);

  /**
   * Realiza registro de novo founder
   */
  const register = useCallback(async (userData) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(userData),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || "Erro ao criar conta");
    }

    const data = await res.json();
    
    // Após registro, faz login automaticamente
    await login(userData.email, userData.password);

    return data;
  }, [login]);

  /**
   * Realiza logout
   */
  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    router.push("/login");
  }, [router]);

  /**
   * Retorna headers de autenticação para requisições
   */
  const getAuthHeaders = useCallback(() => {
    if (!token) return {};
    return {
      Authorization: `Bearer ${token}`,
    };
  }, [token]);

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user,
    isAdmin: user?.role === "admin",
    isFounder: user?.role === "founder",
    login,
    register,
    logout,
    getAuthHeaders,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook para usar o contexto de autenticação
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de um AuthProvider");
  }
  return context;
}

/**
 * Funções de API autenticadas
 */
export async function authFetch(path, options = {}, token) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (res.status === 401) {
    // Token expirado ou inválido
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.href = "/login";
    throw new Error("Sessão expirada. Faça login novamente.");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail || `Erro ${res.status}`);
  }

  // Verifica se há conteúdo para parsear
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return res.json();
  }

  return res;
}
