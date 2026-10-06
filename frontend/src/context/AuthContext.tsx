"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User, UserRole } from "@/lib/types";
import { api, setAuthToken, getAuthToken } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  role: UserRole;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string, role?: UserRole) => Promise<void>;
  demoLogin: (role: UserRole) => Promise<void>;
  logout: () => void;
  isAuthModalOpen: boolean;
  authModalTab: "login" | "signup";
  openAuthModal: (tab?: "login" | "signup") => void;
  closeAuthModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "signup">("login");

  // On mount: restore session or initialize default demo session
  useEffect(() => {
    let isMounted = true;

    const initAuth = async () => {
      try {
        const storedToken = getAuthToken();
        if (storedToken) {
          const profile = await api.getMe();
          if (isMounted) {
            setUser(profile);
            setToken(storedToken);
            setIsLoading(false);
            return;
          }
        }
      } catch {
        // Stored token expired or invalid; fallback to default demo
      }

      // Auto-initialize demo Admin session so dashboard is immediately live
      try {
        const demoRes = await api.demoLogin("admin");
        if (isMounted) {
          setUser(demoRes.user);
          setToken(demoRes.access_token);
        }
      } catch {
        // Backend offline or warming up
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.login({ email, password });
      setUser(res.user);
      setToken(res.access_token);
      setIsAuthModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (
    email: string,
    password: string,
    fullName?: string,
    role: UserRole = "analyst"
  ) => {
    setIsLoading(true);
    try {
      const res = await api.signup({
        email,
        password,
        full_name: fullName,
        role,
      });
      setUser(res.user);
      setToken(res.access_token);
      setIsAuthModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async (targetRole: UserRole) => {
    setIsLoading(true);
    try {
      const res = await api.demoLogin(targetRole);
      setUser(res.user);
      setToken(res.access_token);
      setIsAuthModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.logout();
    setUser(null);
    setToken(null);
  };

  const openAuthModal = (tab: "login" | "signup" = "login") => {
    setAuthModalTab(tab);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const currentRole: UserRole = user?.role || "viewer";

  return (
    <AuthContext.Provider
      value={{
        user,
        role: currentRole,
        token,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        demoLogin,
        logout,
        isAuthModalOpen,
        authModalTab,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
