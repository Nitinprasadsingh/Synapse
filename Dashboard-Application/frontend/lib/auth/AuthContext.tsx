"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User, UserRole, AuthToken } from "@/types";
import { endpoints } from "@/lib/api/endpoints";

interface AuthContextType {
  user: User | null;
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<AuthToken>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");

    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        // Verify current user with backend
        endpoints.getCurrentUser()
          .then((freshUser) => {
            setUser(freshUser);
            localStorage.setItem("user", JSON.stringify(freshUser));
          })
          .catch(() => {
            // Token expired or invalid
            logout();
          })
          .finally(() => {
            setIsLoading(false);
          });
      } catch {
        logout();
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
      if (pathname && !pathname.startsWith("/login") && pathname !== "/") {
        router.push("/login");
      }
    }
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await endpoints.login({ email, password: pass });
    localStorage.setItem("token", res.access_token);
    const userObj: User = {
      id: res.user_id,
      email: res.email,
      full_name: res.full_name,
      role: res.role,
      is_active: true,
      created_at: new Date().toISOString(),
    };
    localStorage.setItem("user", JSON.stringify(userObj));
    setToken(res.access_token);
    setUser(userObj);
    return res;
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user ? user.role : null,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
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
