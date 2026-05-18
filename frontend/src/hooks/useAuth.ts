import { useState, useEffect } from "react";
import { authApi, resourcesApi } from "../api/client";
import type { User } from "../types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      resourcesApi.getMe().then(({ data }) => {
        setUser(data);
        setIsAuthenticated(true);
      }).catch(() => {
        localStorage.clear();
        setIsAuthenticated(false);
      });
    }
  }, []);

  const login = async (username: string, password: string) => {
    const { data } = await authApi.login({ username, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setUser(data.user);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.clear();
    setUser(null);
    setIsAuthenticated(false);
  };

  return { user, isAuthenticated, login, logout };
}